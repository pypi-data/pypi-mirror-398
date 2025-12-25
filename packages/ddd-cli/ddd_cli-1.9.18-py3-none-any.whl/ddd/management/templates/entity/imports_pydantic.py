from pydantic import BaseModel, ConfigDict, Field, validator, model_validator, field_validator
from typing import Optional, List, Dict, Any, ClassVar
from typing_extensions import Self
from uuid import UUID
from datetime import datetime
from .[[ entity_name.lower() ]]_exceptions import *
from .[[ entity_name.lower() ]]_schemas import FileData, BaseEntity