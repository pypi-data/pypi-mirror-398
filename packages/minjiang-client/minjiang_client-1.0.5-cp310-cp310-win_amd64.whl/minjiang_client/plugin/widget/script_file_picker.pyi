from dataclasses import dataclass
from fastapi import APIRouter
from typing import Callable

__all__ = ['OrganizationContext', 'ScriptFilePickerService', 'create_script_file_picker_router', 'get_script_picker_frontend_script']

JsonDict = dict[str, object]

@dataclass
class OrganizationContext:
    organization_id: int
    organization_name: str
    @property
    def root_path(self) -> str: ...

class ScriptFilePickerService:
    def __init__(self, context: OrganizationContext) -> None: ...
    def list_entries(self, parent_dir_id: int | None, parent_path: str | None) -> JsonDict: ...

def get_script_picker_frontend_script() -> str: ...
def create_script_file_picker_router(context_provider: Callable[[], OrganizationContext | dict[str, object]]) -> APIRouter: ...
