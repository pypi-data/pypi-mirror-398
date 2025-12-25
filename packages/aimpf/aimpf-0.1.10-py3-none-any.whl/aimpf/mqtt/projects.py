import os
import logging
import requests
from enum import Enum
from pydantic import BaseModel, Field, model_validator, model_serializer
from typing import Any
from warnings import warn


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


class Sponsor(BaseModel):
    id: int=Field(..., alias="sponsorId")
    name: str=Field(..., alias="sponsorName")
    description: str=Field(..., alias="sponsorDescription")
    label: str=Field(..., alias="sponsorLabel")


class Project(BaseModel):
    id: int=Field(..., alias="projectId")
    name: str=Field(..., alias="projectName")
    description: str=Field(..., alias="projectDescription")
    abbrev: str=Field(..., alias="projectDescriptionLabel")
    label: str=Field(..., alias="projectLabel")


class ProjectApiEntry(BaseModel):
    project: Project
    sponsor: Sponsor

    @model_serializer
    def serialize(self):
        return {
            **self.project.model_dump(by_alias=True),
            **self.sponsor.model_dump(by_alias=True),
        }

    @model_validator(mode="before")
    @classmethod
    def validate_project(cls, data) -> dict[str, Any]:
        sponsor = {k:v for k,v in data.items() if k.startswith("sponsor")}
        project = {k:v for k,v in data.items() if k.startswith("project")}
        return {
            "project": Project(**project),
            "sponsor": Sponsor(**sponsor),
        }
    
    def __str__(self) -> str:
        return self.label
    
    @property
    def id(self) -> int:
        return self.project.id
    
    @property
    def label(self) -> str:
        return self.project.label


class ProjectEnumFactory:
    HOST = "https://ui80i29qbb.execute-api.us-east-1.amazonaws.com/v1/projects"
    # These are extra projects currently not included in the project list retrieved
    # from Andy's API. Ideally, we want Andy to update his end, but this temporary
    # solution at least allows us to test with our credentials for now.
    ADMIN_PROJECTS = [
        ProjectApiEntry(**{
            "projectId": 1002,
            "projectName": "MQTT Error Monitoring",
            "projectDescription": "Project for capturing and logging MQTT connection errors.",
            "projectDescriptionLabel": "ERROR/mqtt",
            "sponsorId": 1002,
            "sponsorName": "MQTT Error Handler",
            "sponsorDescription": "System component for MQTT error reporting",
            "sponsorLabel": "mqtt-error",
            "projectLabel": "ERROR/mqtt",
        })
    ]
    TEST_PROJECTS = [
        ProjectApiEntry(**{
            "projectId": 1001,
            "projectName": "Test Project",
            "projectDescription": "Dummy project used solely for testing.",
            "projectDescriptionLabel": "test-project",
            "sponsorId":7,
            "sponsorName": "Contextualize",
            "sponsorDescription": "Contexualize LLC",
            "sponsorLabel": "contextualize",
            "projectLabel": "test-project---contextualize"
        }),
        ProjectApiEntry(**{
            "projectId": 1001,
            "projectName": "Test Project",
            "projectDescription": "Dummy project used solely for testing.",
            "projectDescriptionLabel": "test-project",
            "sponsorId": 1001,
            "sponsorName": "Matthew Kosmala",
            "sponsorDescription": "Software developer at GT",
            "sponsorLabel": "matthew",
            "projectLabel": "test-project---matthew",
        })
    ]

    def __new__(cls,
                projects: list[ProjectApiEntry] | None=None,
                *,
                admin: bool=True,
                test: bool=False):
        """
        When instantiated, this returns a new Enum class that can be used to
        reference projects. It is a factory function that returns a new class
        definition each time it is called with the projects defined in the host
        database at the moment of instantiation, because the Enum class is
        immutable and cannot be modified after it is created.

        Parameters
        ----------
        projects : list[ProjectApiEntry] | None
            If provided, only the listed projects will be included in the
            enumeration. When None (the default), projects are retrieved from
            the host database.
        admin : bool
            Whether to include additional administrative projects.
            Default: True.
        test : bool
            Whether to include test additional test project. Default: False.

        Returns
        -------
        Enum
            An Enum class that can be used to reference projects.

        Examples
        --------
        Generate a new Enum, including additional administrative projects.
        
            Project = ProjectEnumFactory()

        Generate a new project Enum, excluding additional administrative projects.
        
            Project = ProjectEnumFactory(admin=False)
        
        Generate a new project Enum, including additional test projects.
        
            Project = ProjectEnumFactory(test=True)
        """
        def string_function(self) -> str:
            return self.value.label
    
        if projects is None:
            projects = ProjectEnumFactory.get_projects()
        if admin:
            projects.extend(ProjectEnumFactory.ADMIN_PROJECTS)
        if test:
            projects.extend(ProjectEnumFactory.TEST_PROJECTS)
        ProjectEnum = Enum("ProjectEnum",
                    {
                        project.label: project
                        for project in projects
                    })
        ProjectEnum.__str__ = string_function  # type: ignore[reportAttributeAccessError]
        return ProjectEnum
    
    @staticmethod
    def get_projects() -> list[ProjectApiEntry]:
        try:
            response = requests.get(ProjectEnumFactory.HOST)
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"Failed to get projects: {e}")
            raise
        projects = response.json()
        return [ProjectApiEntry(**project) for project in projects]
    

def get_projects() -> list[ProjectApiEntry]:
    warn("Use `ProjectEnumFactory.get_projects()` instead.", DeprecationWarning)
    return ProjectEnumFactory.get_projects()


def project_enumeration_factory() -> Enum:
    warn("Use `ProjectEnumFactory()` instead.", DeprecationWarning)
    return ProjectEnumFactory()
