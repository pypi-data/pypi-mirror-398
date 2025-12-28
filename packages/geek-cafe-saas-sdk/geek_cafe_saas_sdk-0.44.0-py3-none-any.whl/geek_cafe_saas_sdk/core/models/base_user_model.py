"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.
"""


from geek_cafe_saas_sdk.core.models.base_model import BaseModel

class BaseUserModel(BaseModel):
    """
    The Base DB Model for models that have a user tied to them
    """
    
    # Require user_id to be set before saving
    _required_properties = ["user_id"]

    def __init__(self) -> None:
        super().__init__()                
        self._user_id: str | None = None        
        # Note: tenant_id = organization/company, owner_id = specific user within tenant
        self._owner_id: str | None = None  # User ID who owns this file
    
    def validate_required_properties(self) -> None:
        if not self.user_id and hasattr(self, 'owner_id') and self.owner_id:
            self.user_id = self.owner_id
            
        super().validate_required_properties()

    @property
    def user_id(self)  -> str | None:
        return self._user_id
    
    @user_id.setter
    def user_id(self, value: str | None):
        self._user_id = value

    # Properties - Ownership
    @property
    def owner_id(self) -> str | None:
        """
        User ID who owns the file (not tenant_id - that's the organization).
        If owner_id is not set, use user_id.
        An owner can be different than the user_id, if there was a transfer of ownership or
        if the file was created by a different user for another user.        
        """
        return self._owner_id or self.user_id
    
    @owner_id.setter
    def owner_id(self, value: str | None):
        self._owner_id = value