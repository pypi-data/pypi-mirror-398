"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.
"""

from geek_cafe_saas_sdk.core.models.base_model import BaseModel

class BaseTenantModel(BaseModel):
    """
    The Base DB Model for models that have a tenant tied to them
    """
    
    # Require tenant_id to be set before saving
    _required_properties = ["tenant_id"]

    def __init__(self) -> None:
        super().__init__()
        self.tenant_id: str | None = None
       