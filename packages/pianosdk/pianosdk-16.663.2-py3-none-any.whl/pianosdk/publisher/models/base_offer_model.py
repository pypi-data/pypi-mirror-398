from datetime import date, datetime
from pydantic.main import BaseModel
from typing import Optional
from pianosdk.publisher.models.term import Term
from pianosdk.publisher.models.upgrade_option import UpgradeOption
from pianosdk.publisher.models.user import User
from typing import List


class BaseOfferModel(BaseModel):
    offer_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    create_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    create_by: Optional['User'] = None
    update_by: Optional['User'] = None
    terms: Optional['List[Term]'] = None
    upgrade_options: Optional['List[UpgradeOption]'] = None


BaseOfferModel.model_rebuild()
