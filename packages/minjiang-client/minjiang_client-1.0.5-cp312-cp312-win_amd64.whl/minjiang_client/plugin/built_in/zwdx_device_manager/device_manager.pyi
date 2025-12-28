from fastapi import FastAPI
from minjiang_client.com.command import get_command_print as get_command_print, get_command_status as get_command_status, submit_command as submit_command
from minjiang_client.group.cloud_group import CloudGroup as CloudGroup
from minjiang_client.plugin.parent_process_monitor import setup_parent_process_monitor as setup_parent_process_monitor
from pydantic import BaseModel
from typing import Any

def get_template_path(template_name: str) -> str: ...
def load_html_template(template_name: str, **kwargs) -> str: ...

class AddDeviceRequest(BaseModel):
    name: str
    model: str
    sn: str | None
    create_uid: int | None
    configValues: dict[str, Any] | None

class UpdateDeviceRequest(BaseModel):
    sn: str
    name: str | None
    configValues: dict[str, Any] | None

class ConfigFileRequest(BaseModel):
    filename: str
    content: str | None

def create_utility_app(utility_name: str, config: dict) -> FastAPI: ...
