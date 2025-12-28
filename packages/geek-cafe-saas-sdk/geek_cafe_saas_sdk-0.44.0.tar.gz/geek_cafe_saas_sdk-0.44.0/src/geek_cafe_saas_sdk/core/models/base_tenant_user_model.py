"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.
"""

from geek_cafe_saas_sdk.core.models.base_tenant_model import BaseTenantModel
from geek_cafe_saas_sdk.core.models.base_user_model import BaseUserModel

class BaseTenantUserModel(BaseTenantModel, BaseUserModel):
    """
    The Base DB Model
    Sets a common set of properties for all models
    """
    
    # Require both tenant_id and user_id to be set before saving
    _required_properties = ["tenant_id", "user_id"]

    def __init__(self) -> None:
        # Use cooperative multiple inheritance
        super().__init__()
        # Properties are already initialized by parent classes via MRO
        