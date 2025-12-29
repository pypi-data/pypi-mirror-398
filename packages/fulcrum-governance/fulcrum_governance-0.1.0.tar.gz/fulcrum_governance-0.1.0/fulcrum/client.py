import grpc
import uuid
import time
import atexit
import threading
from queue import Queue, Empty
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.struct_pb2 import Struct

# Import generated gRPC code
from fulcrum.eventstore.v1 import eventstore_pb2
from fulcrum.eventstore.v1 import eventstore_pb2_grpc
from fulcrum.policy.v1 import policy_service_pb2
from fulcrum.policy.v1 import policy_service_pb2_grpc

import logging

# Configure default logging
logger = logging.getLogger("fulcrum")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class FulcrumClient:
    def __init__(self, 
                 host: str = "localhost:50051", 
                 api_key: Optional[str] = None,
                 on_failure: str = "FAIL_OPEN",
                 timeout_ms: int = 500):
        self.host = host
        self.api_key = api_key
        self.on_failure = on_failure.upper() # FAIL_OPEN or FAIL_CLOSED
        self.timeout_ms = timeout_ms
        self.channel = None
        self.stub = None
        self.policy_stub = None
        self.queue = Queue()
        self.middlewares = []
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._connect()
        self._worker_thread.start()
        
        # Ensure clean shutdown
        atexit.register(self.shutdown)

    def add_middleware(self, func):
        """Adds a middleware function that can inspect or modify events before they are queued.
        Func signature: (event_type, payload) -> (event_type, payload)
        If func returns None, the event is dropped.
        """
        self.middlewares.append(func)

    def _connect(self):
        """Initializes or re-establishes the gRPC connection."""
        try:
            if self.channel:
                self.channel.close()
            
            if self.host.endswith(":443"):
                creds = grpc.ssl_channel_credentials()
                self.channel = grpc.secure_channel(self.host, creds)
            else:
                self.channel = grpc.insecure_channel(self.host)
            
            self.stub = eventstore_pb2_grpc.EventStoreServiceStub(self.channel)
            self.policy_stub = policy_service_pb2_grpc.PolicyServiceStub(self.channel)
            logger.debug(f"Connected to Fulcrum at {self.host}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")

    def _metadata(self):
        metadata = []
        if self.api_key:
            metadata.append(("x-api-key", self.api_key))
        return metadata

    def _worker(self):
        """Background worker to process the event queue."""
        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                # Wait for an event with a timeout to check stop_event
                req = self.queue.get(timeout=1.0)
                self._publish_with_retry(req)
                self.queue.task_done()
            except Empty:
                continue
            except Exception as e:
                # If we are stopping, ignore channel closed errors
                if self._stop_event.is_set() and ("closed channel" in str(e) or isinstance(e, ValueError)):
                     logger.debug(f"Worker shutting down, ignoring error: {e}")
                     return
                logger.error(f"Worker Error: {e}")

    def _publish_with_retry(self, req, attempts=5):
        """Attempts to publish with exponential backoff and reconnection."""
        for i in range(attempts):
            try:
                self.stub.PublishEvent(req, metadata=self._metadata())
                return
            except grpc.RpcError as e:
                if i < attempts - 1:
                    wait_time = (2 ** i) + 0.1 # Exponential backoff: 0.1, 2.1, 4.1, 8.1...
                    logger.warning(f"Publish failed (attempt {i+1}/{attempts}): {e.code()}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    if e.code() in [grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.INTERNAL]:
                        self._connect() # Try reconnecting
                else:
                    logger.error(f"Final attempt failed for event: {e.code()} - {e.details()}")

    def _evaluate_policy(self, req: policy_service_pb2.EvaluatePolicyRequest) -> policy_service_pb2.EvaluatePolicyResponse:
        """Evaluates a policy synchronously with fail-safe logic."""
        try:
            return self.policy_stub.EvaluatePolicy(
                req, 
                timeout=self.timeout_ms / 1000.0,
                metadata=self._metadata()
            )
        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            # Fail-safe logic
            if self.on_failure == "FAIL_OPEN":
                logger.warning("Failing OPEN: allowing execution despite governance error.")
                return policy_service_pb2.EvaluatePolicyResponse(
                    decision="ALLOW",
                    reason=f"Fail-safe: {str(e)}"
                )
            else:
                logger.error("Failing CLOSED: blocking execution due to governance error.")
                return policy_service_pb2.EvaluatePolicyResponse(
                    decision="DENY",
                    reason=f"Fail-safe (Closed): {str(e)}"
                )

    def shutdown(self):
        """Cleanly shuts down the worker and flushes the queue."""
        self._stop_event.set()
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5.0)
        if self.channel:
            self.channel.close()

    @contextmanager
    def envelope(self, 
                 workflow_id: str = "default-workflow", 
                 execution_id: Optional[str] = None,
                 tenant_id: str = "default-tenant",
                 metadata: Optional[Dict[str, str]] = None) -> Generator['Envelope', None, None]:
        
        if not execution_id:
            execution_id = str(uuid.uuid4())
            
        envelope = Envelope(client=self, 
                            execution_id=execution_id, 
                            tenant_id=tenant_id, 
                            workflow_id=workflow_id)
        
        # Log Start
        envelope.log("execution_started", {"started_at": time.time()})
        
        try:
            yield envelope
            # Log Success
            envelope.log("execution_completed", {"status": "success"})
        except Exception as e:
            # Log Failure
            envelope.log("execution_failed", {"error": str(e)})
            raise e

class Envelope:
    def __init__(self, client: 'FulcrumClient', execution_id: str, tenant_id: str, workflow_id: str):
        self.client = client
        self.execution_id = execution_id
        self.tenant_id = tenant_id
        self.workflow_id = workflow_id
        self.envelope_id = str(uuid.uuid4()) # Trace grouping

    def guard(self, action_name: str, input_text: str = "", metadata: Optional[Dict[str, str]] = None) -> bool:
        """A synchronous barrier that evaluates policies before an action.
        Returns True if allowed, False if denied.
        """
        self.log(f"guard_check_started", {"action": action_name, "input": input_text})
        
        # Prepare context attributes
        attrs = metadata or {}
        
        req = policy_service_pb2.EvaluatePolicyRequest(
            context=policy_service_pb2.EvaluationContext(
                tenant_id=self.tenant_id,
                workflow_id=self.workflow_id,
                input_text=input_text,
                attributes=attrs
            )
        )

        res = self.client._evaluate_policy(req)
        
        self.log(f"guard_check_completed", {
            "action": action_name, 
            "decision": res.decision,
            "reason": res.reason
        })

        return res.decision == "ALLOW"

    def log(self, event_type: str, payload: Dict[str, Any] = {}):
        """Logs an event to Fulcrum asynchronously."""
        
        # Apply middlewares
        for mw in self.client.middlewares:
            result = mw(event_type, payload)
            if result is None:
                logger.debug(f"Event {event_type} dropped by middleware")
                return
            event_type, payload = result

        # Convert dict to Struct
        payload_struct = Struct()
        try:
            payload_struct.update(payload)
        except Exception as e:
            logger.warning(f"Failed to serialize payload: {e}")

        ts = Timestamp()
        ts.GetCurrentTime()

        req = eventstore_pb2.PublishEventRequest(
            event=eventstore_pb2.EventPayload(
                execution_id=self.execution_id,
                envelope_id=self.envelope_id,
                tenant_id=self.tenant_id,
                workflow_id=self.workflow_id,
                event_type=event_type,
                timestamp=ts,
                payload=payload_struct
            )
        )
        
        if not self.client._stop_event.is_set():
            self.client.queue.put(req)
        else:
            # Fallback for sync publish during shutdown if absolutely needed
            # but usually we just let the worker flush what's already in the queue
            pass
