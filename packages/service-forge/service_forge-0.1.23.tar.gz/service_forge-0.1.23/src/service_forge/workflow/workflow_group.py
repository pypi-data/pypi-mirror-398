import uuid
from service_forge.workflow.workflow import Workflow

WORKFLOW_DEFAULT_VERSION = "0"
WORKFLOW_MAIN_WORKFLOW_NAME = "main"

class WorkflowGroup:
    def __init__(
        self,
        workflows: list[Workflow],
        main_workflow_name: str = WORKFLOW_MAIN_WORKFLOW_NAME,
        main_workflow_version: str = WORKFLOW_DEFAULT_VERSION,
    ) -> None:
        self.workflows = workflows
        self.main_workflow_name = main_workflow_name
        self.main_workflow_version = main_workflow_version

    def add_workflow(self, workflow: Workflow) -> None:
        self.workflows.append(workflow)

    def get_workflow_by_name(self, name: str, version: str) -> Workflow | None:
        for workflow in self.workflows:
            if workflow.name == name and workflow.version == version:
                return workflow
        return None

    def get_workflow_by_id(self, id: uuid.UUID) -> Workflow | None:
        for workflow in self.workflows:
            print(workflow.name, workflow.id, id)
            if workflow.id == id:
                return workflow
        return None

    def get_main_workflow(self, allow_none: bool = True) -> Workflow | None:
        workflow = self.get_workflow_by_name(self.main_workflow_name, self.main_workflow_version)
        if not allow_none and workflow is None:
            raise ValueError(f"Main workflow with name {self.main_workflow_name} and version {self.main_workflow_version} not found in workflow group.")
        return workflow

    async def run(self, name: str = None, version: str = None, id: uuid.UUID = None) -> None:
        if name is None and id is None:
            workflow = self.get_main_workflow()
        elif name is not None:
            workflow = self.get_workflow_by_name(name, version)
        elif id is not None:
            workflow = self.get_workflow_by_id(id)
        else:
            workflow = None
        if workflow is None:
            raise ValueError(f"Workflow with name {name} and version {version} and id {id} not found in workflow group.")
        await workflow.run()