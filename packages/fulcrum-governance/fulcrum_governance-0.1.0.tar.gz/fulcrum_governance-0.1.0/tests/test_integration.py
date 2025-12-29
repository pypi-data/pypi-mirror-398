import pytest
import uuid
import time
from fulcrum.client import FulcrumClient

# Configuration
# Assuming server is running locally on default port
FULCRUM_ADDR = "127.0.0.1:50051"
API_KEY = "test-api-key-a" # Tenant A
TENANT_ID = "3a352055-64d1-443b-a916-d35d97f8c055"

@pytest.fixture
def client():
    # In a real scenario, we might want to check connectivity first
    client = FulcrumClient(host=FULCRUM_ADDR, api_key=API_KEY)
    yield client
    client.shutdown()

def test_client_connectivity(client):
    """Verify client can connect and create a simple envelope."""
    workflow_id = f"test-workflow-{uuid.uuid4()}"
    execution_id = f"test-exec-{uuid.uuid4()}"
    
    try:
        with client.envelope(workflow_id=workflow_id, execution_id=execution_id) as env:
             assert env.envelope_id is not None
             assert env.execution_id == execution_id
    except Exception as e:
        pytest.fail(f"Failed to create envelope: {e}")

def test_full_workflow_logging(client):
    """Verify sending events within an envelope."""
    workflow_id = "integration-test-wf"
    execution_id = f"integ-{uuid.uuid4()}"
    
    with client.envelope(workflow_id=workflow_id, execution_id=execution_id) as env:
        # 1. Log generic event
        env.log("execution_started", {"input": "test-data"})
        
        # 2. Log tool call
        env.log("tool_call", {
            "tool": "calculator",
            "input": "2+2",
            "status": "success"
        })
        
        # 3. Log completion (implicit in context manager exit, but usually we log explicit result)
        env.log("execution_completed", {"result": "4"})

    # TODO: We could query the EventStore to verify persistence if we had a query client here.
    # For now, success means no exceptions raised during gRPC calls.
