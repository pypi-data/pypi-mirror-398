from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator

class UserProducts(BaseModel):
    """Schema for user product settings"""
    qlik_sense_analyzer: bool = Field(..., alias="qlikSenseAnalyzer", description="Whether user has Qlik Sense Analyzer access")
    qlik_sense_professional: bool = Field(..., alias="qlikSenseProfessional", description="Whether user has Qlik Sense Professional access")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class UserCreate(BaseModel):
    """Schema for creating a user"""
    name: str = Field(..., description="User name")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    language: str = Field(..., description="User language preference")
    products: UserProducts = Field(..., description="User product access settings")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = Field(None, description="User name")
    username: Optional[str] = Field(None, description="Username")
    email: Optional[str] = Field(None, description="User email")
    roles: Optional[List[int]] = Field(None, description="List of role IDs to assign")
    language: Optional[str] = Field(None, description="User language preference")
    products: Optional[dict] = Field(None, description="User product access settings")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class UserInvite(BaseModel):
    """Schema for inviting a user"""
    email: str = Field(..., description="User email")
    products: Optional[dict] = Field(None, description="User product access settings")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class QlikDashboardRight(BaseModel):
    """Schema for Qlik dashboard right"""
    guid: str = Field(..., description="Dashboard GUID")
    data_model_edit: bool = Field(..., alias="dataModelEdit", description="Whether data model is editable")
    editable: bool = Field(..., description="Whether dashboard is editable")
    organigrams: List[int] = Field(default_factory=list, description="List of organigram IDs")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class QlikDashboardRightsPayload(BaseModel):
    """Schema for Qlik dashboard rights payload"""
    dashboard_rights: List[QlikDashboardRight] = Field(..., alias="dashboardRights", description="List of dashboard rights")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class DashboardRight(BaseModel):
    """Schema for dashboard right"""
    dashboard_id: int = Field(..., alias="dashboardId", description="Dashboard ID")
    editable: bool = Field(..., description="Whether dashboard is editable")
    organigrams: List[int] = Field(default_factory=list, description="List of organigram IDs")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class DashboardRightsPayload(BaseModel):
    """Schema for dashboard rights payload"""
    dashboard_rights: List[DashboardRight] = Field(..., alias="dashboardRights", description="List of dashboard rights")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class UserEntitiesPayload(BaseModel):
    """Schema for user entities payload"""
    entities: List[int] = Field(..., description="List of entity IDs to assign")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class User(BaseModel):
    """Schema for user data"""
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")

    roles: List[int] = Field(default_factory=list, description="User roles")
    organization_chart_entities: List[int] = Field(default_factory=list, description="Organization chart entities")
    qlik_dashboards: List[dict] = Field(default_factory=list, description="Qlik dashboards")
    dashboards: List[dict] = Field(default_factory=list, description="Standard dashboards")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class QlikAppUserAuthorization(BaseModel):
    """Schema for Qlik app user authorization"""
    username: Optional[str] = None
    user_id: int = Field(alias="userId")
    entity_codes: List[str] = Field(default_factory=list, alias="entityCodes")

    class Config:
        frozen = True
        populate_by_name = True
