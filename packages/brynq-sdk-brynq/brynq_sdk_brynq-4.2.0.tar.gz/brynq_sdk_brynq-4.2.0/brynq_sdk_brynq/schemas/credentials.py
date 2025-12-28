from typing import Dict, Any, List
from pydantic import BaseModel, Field, RootModel


class CredentialData(RootModel[Dict[str, Any]]):
    """Schema for credential data which can contain any key-value pairs"""
    root: Dict[str, Any]

    class Config:
        frozen = True
        strict = False


class CredentialSource(BaseModel):
    """Schema for a credential source or target"""
    app: str = Field(..., description="Application identifier")
    type: str = Field(..., description="Type of the credential source/target")
    data: Dict[str, Any] = Field(..., description="Credential data key-value pairs")
    direction: str = Field(..., description="Direction of the credential flow (source/target)")

    class Config:
        frozen = True
        strict = False
        populate_by_name = True
        extra = 'allow'


class CredentialsConfig(BaseModel):
    """Schema for the complete credentials configuration"""
    sources: List[CredentialSource] = Field(..., description="List of credential sources")
    targets: List[CredentialSource] = Field(..., description="List of credential targets")

    class Config:
        frozen = True
        strict = False
        populate_by_name = True
        extra = 'allow'
