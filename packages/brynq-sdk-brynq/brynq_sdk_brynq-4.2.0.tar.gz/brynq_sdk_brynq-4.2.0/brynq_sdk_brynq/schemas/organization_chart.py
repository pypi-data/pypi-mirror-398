from typing import List, Optional
from pydantic import BaseModel, Field


class OrganizationChartNode(BaseModel):
    """Schema for organization chart node"""
    id: int = Field(..., description="Node ID")
    name: str = Field(..., description="Node name")
    drop_index: int = Field(..., alias="dropIndex", description="Drop index for ordering")
    parent_id: Optional[int] = Field(None, alias="parent_id", description="Parent node ID, null for root nodes")
    source_system_entities: List[str] = Field(default_factory=list, alias="source_system_entities", description="List of source system entities")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class OrganizationLayerCreate(BaseModel):
    """Schema for organization layer input"""
    name: str = Field(..., description="Layer name")
    level: int = Field(..., ge=0, description="Layer level in hierarchy")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class OrganizationLayerUpdate(BaseModel):
    """Schema for organization layer response"""
    id: int = Field(..., description="Layer ID")
    level: int = Field(None, ge=0, description="Layer level in hierarchy")
    name: str = Field(None, description="Layer name")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class OrganizationLayerGet(OrganizationLayerUpdate):
    pass


class OrganizationNode(BaseModel):
    """Schema for organization chart node"""
    id: int = Field(..., description="Node ID")
    name: str = Field(..., description="Node name")
    parent_id: Optional[int] = Field(None, alias="parentId", description="Parent node ID")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class OrganizationNodeCreate(BaseModel):
    """Schema for creating organization chart node"""
    name: str = Field(..., description="Node name")
    parent_id: Optional[int] = Field(None, alias="parentId", description="Parent node ID")
    position: Optional[int] = Field(None, description="Position among siblings")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class OrganizationNodeUpdate(OrganizationNodeCreate):
    id: int = Field(..., description="Node ID")