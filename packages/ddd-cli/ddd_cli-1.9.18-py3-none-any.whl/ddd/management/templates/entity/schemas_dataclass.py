from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4

@dataclass
class FileData:
    file_name: Optional[str] = None
    url: Optional[str] = None