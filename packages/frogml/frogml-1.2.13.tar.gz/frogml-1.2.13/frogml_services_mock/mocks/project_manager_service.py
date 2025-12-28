from typing import Dict, Optional
from uuid import uuid4

from google.protobuf.timestamp_pb2 import Timestamp
from grpc import ServicerContext

from frogml._proto.qwak.projects.projects_pb2 import (
    GetProjectRequest,
    GetProjectResponse,
    Project,
    ProjectSpec, CreateProjectRequest, CreateProjectResponse,
)
from frogml._proto.qwak.projects.projects_pb2_grpc import (
    ProjectsManagementServiceServicer,
)


class ProjectManagerServiceMock(ProjectsManagementServiceServicer):
    def __init__(self):
        self.model_group_specs_by_name: Dict[str, ProjectSpec] = {}

    def CreateProject(
        self, request: CreateProjectRequest, _: Optional[ServicerContext]
    ) -> CreateProjectResponse:
        if request.project_name in self.model_group_specs_by_name.keys():
            description = f"Project with name {request.project_name} already exists"
            raise Exception(description)

        now = Timestamp()
        now.GetCurrentTime()

        model_group_spec = ProjectSpec(
            project_id=str(uuid4()),
            project_name=request.project_name,
            project_description=request.project_description,
            project_status=ProjectSpec.Status.ACTIVE,
            created_at=now,
            last_modified_at=now,
            models_active=0,
            models_count=0,
        )

        self.model_group_specs_by_name[request.project_name] = model_group_spec

        return CreateProjectResponse(project=model_group_spec)

    def GetProject(self, request: GetProjectRequest, _: Optional[ServicerContext]) -> GetProjectResponse:
        if not request.project_id and not request.project_name:
            description: str = "Either project_id or project_name must be provided"
            raise Exception(description)

        if request.project_id:
            matched_model_groups: list[ProjectSpec] = list(
                filter(
                    lambda project: request.project_id == project.project_id,
                    self.model_group_specs_by_name.values(),
                )
            )
        else:  # request.project_name
            matched_model_groups = list(
                filter(
                    lambda project: request.project_name == project.project_name,
                    self.model_group_specs_by_name.values(),
                )
            )

        if matched_model_groups:
            return GetProjectResponse(project=Project(spec=matched_model_groups[0]))

        description: str = f"Project with id {request.project_name} was not found"
        raise Exception(description)
