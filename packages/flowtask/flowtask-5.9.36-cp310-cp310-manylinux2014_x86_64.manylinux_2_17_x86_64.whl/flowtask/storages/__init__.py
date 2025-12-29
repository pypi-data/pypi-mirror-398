"""
Storages.

Storages covering the ways to store the data processed by the tasks and the task/hooks definitions.

FileStore: how Flowtask can store files in the filesystem.
TaskStorage: how Flowtask can store the task definitions (yaml, json files).
"""
from .files import FileStore
from .tasks import (
    FileTaskStorage,
    RowTaskStorage,
    MemoryTaskStorage,
    DatabaseTaskStorage,
    GitTaskStorage
)
