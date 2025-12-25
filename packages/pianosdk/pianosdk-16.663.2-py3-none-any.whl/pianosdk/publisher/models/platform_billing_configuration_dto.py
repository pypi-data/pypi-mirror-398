from datetime import date, datetime
from pydantic.main import BaseModel
from typing import Optional


class PlatformBillingConfigurationDTO(BaseModel):
    platform_billing_configuration_id: Optional[str] = None
    aid: Optional[str] = None
    account_id: Optional[str] = None
    properties: Optional[str] = None


PlatformBillingConfigurationDTO.model_rebuild()
