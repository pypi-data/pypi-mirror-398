from enum import Enum


class AccessTypes(str, Enum):
    READ = 'read'
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
