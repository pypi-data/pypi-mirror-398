from enum import Enum

class States(Enum):
    NEW = "New"
    MODIFIED = "Modified"
    UNCHANGED = "Unchanged"
    REMOVED = "Removed"