from datetime import date, datetime
from pydantic.main import BaseModel
from typing import Optional
from pianosdk.publisher.models.resource import Resource
from typing import List


class AddressUsageInfo(BaseModel):
    is_locked: Optional[bool] = None
    has_usages: Optional[bool] = None
    resources: Optional['List[Resource]'] = None


AddressUsageInfo.model_rebuild()
