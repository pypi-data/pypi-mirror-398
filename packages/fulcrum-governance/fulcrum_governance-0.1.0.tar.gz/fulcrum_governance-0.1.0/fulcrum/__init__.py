"""
Fulcrum SDK - Intelligent AI Governance for Enterprise Agents

Usage:
    from fulcrum import FulcrumClient

    client = FulcrumClient(host="localhost:50051", api_key="your-key")
    
    with client.envelope(workflow_id="my-workflow") as env:
        if env.guard("sensitive_action", input_text=user_input):
            # Proceed with action
            env.log("action_executed", {"result": "success"})
"""

__version__ = "0.1.0"
__author__ = "Fulcrum Team"

from .client import FulcrumClient, Envelope

__all__ = ["FulcrumClient", "Envelope", "__version__"]
