from datetime import date, datetime
from pydantic.main import BaseModel
from typing import Optional


class Mandate(BaseModel):
    next_charge_date: Optional[datetime] = None
    reference: Optional[str] = None
    id: Optional[str] = None


Mandate.model_rebuild()
