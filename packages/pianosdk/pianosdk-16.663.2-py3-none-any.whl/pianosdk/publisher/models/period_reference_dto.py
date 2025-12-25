from datetime import date, datetime
from pydantic.main import BaseModel
from typing import Optional


class PeriodReferenceDTO(BaseModel):
    index_in_array: Optional[int] = None
    period_pub_id: Optional[str] = None


PeriodReferenceDTO.model_rebuild()
