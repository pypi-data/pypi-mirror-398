from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, validator, model_validator, field_validator
from typing import Dict, List, Optional, Any
from typing_extensions import Self