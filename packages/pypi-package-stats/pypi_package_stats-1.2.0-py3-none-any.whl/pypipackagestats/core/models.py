
from dataclasses import dataclass


@dataclass
class ProjectMetadata:
    name: str
    version: str
    repository_url: str
    author: str
    author_url: str