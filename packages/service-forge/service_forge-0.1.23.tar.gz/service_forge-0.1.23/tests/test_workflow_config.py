import pytest
from service_forge.workflow.workflow_factory import create_workflow

@pytest.mark.asyncio
async def test_if_workflow_config():
    """Test if node in workflow config."""
    print()
    workflow = create_workflow("configs/test_if.yaml")
    await workflow.run()