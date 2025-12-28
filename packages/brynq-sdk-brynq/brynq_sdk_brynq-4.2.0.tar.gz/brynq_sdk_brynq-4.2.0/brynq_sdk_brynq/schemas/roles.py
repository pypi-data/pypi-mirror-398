from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any, Dict

class DashboardRight(BaseModel):
    """Schema for dashboard rights"""
    dashboard_id: int = Field(..., alias="dashboardId", description="ID of the dashboard")
    editable: bool = Field(..., description="Whether the dashboard is editable")
    entities: List[int] = Field(default_factory=list, description="List of entity IDs")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class QlikDashboardRight(BaseModel):
    """Schema for Qlik dashboard rights"""
    guid: str = Field(..., description="Dashboard GUID")
    data_model_editable: bool = Field(..., alias="dataModelEditable", description="Whether the data model is editable")
    editable: bool = Field(..., description="Whether the dashboard is editable")
    entities: List[int] = Field(default_factory=list, description="List of entity IDs")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class CreateRoleRequest(BaseModel):
    """Schema for creating a new role"""
    name: str = Field(..., description="Name of the role")
    dashboards: List[DashboardRight] = Field(default_factory=list, description="List of dashboard rights")
    qlik_dashboards: List[QlikDashboardRight] = Field(default_factory=list, alias="qlikDashboards", description="List of Qlik dashboard rights")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class RoleUser(BaseModel):
    """Schema for users assigned to a role"""
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    active: bool = Field(..., description="Whether the user is active")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class RoleSchema(BaseModel):
    """Schema for role data"""
    id: int = Field(..., description="Unique identifier for the role")
    name: str = Field(..., description="Name of the role")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Role permissions")
    dashboards: List[Dict[str, Any]] = Field(default_factory=list, description="List of dashboard rights")
    qlik_dashboards: List[Dict[str, Any]] = Field(default_factory=list, alias="qlikDashboards", description="List of Qlik dashboard rights")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class RoleSchema(BaseModel):
    """Schema for role data validation"""
    id: int = Field(..., description="Unique identifier for the role", gt=0)
    name: str = Field(None, description="Name of the role")
    dashboards: List[Any] = Field(default_factory=list, description="List of dashboards associated with the role")
    permissions: Optional[Any] = Field(default=None, description="Role permissions")
    qlik_dashboards: List[Any] = Field(default_factory=list, description="List of Qlik dashboards associated with the role")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that the name is not empty or just whitespace"""
        if not v.strip():
            raise ValueError("Role name cannot be empty or just whitespace")
        return v.strip()

    @field_validator('dashboards', 'qlik_dashboards')
    @classmethod
    def validate_dashboard_lists(cls, v: List[Any]) -> List[Any]:
        """Ensure dashboard lists are always lists, even if empty"""
        if v is None:
            return []
        return v

    class Config:
        frozen = True  # Makes the model immutable
        strict = True  # Ensures strict type checking
        populate_by_name = True  # Allows both camelCase and snake_case access
