from pydantic import BaseModel


class PermissionsInfo(BaseModel):
    has_read_permission: bool = True
    has_create_permission: bool = True
    has_update_permission: bool = True
    has_delete_permission: bool = True
