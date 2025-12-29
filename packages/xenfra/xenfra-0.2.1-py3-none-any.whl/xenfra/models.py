from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"

class SourceType(str, Enum):
    LOCAL = "local"
    GIT = "git"

class Deployment(BaseModel):
    id: str = Field(..., description="Unique identifier for the deployment")
    projectId: str = Field(..., description="Identifier of the project being deployed")
    status: DeploymentStatus = Field(..., description="Current status of the deployment")
    source: str = Field(..., description="Source of the deployment (e.g., 'cli', 'api')")
    created_at: datetime = Field(..., description="Timestamp when the deployment was created")
    finished_at: datetime | None = Field(None, description="Timestamp when the deployment finished")

class DeploymentRecord(BaseModel):
    deployment_id: str = Field(..., description="Unique identifier for this deployment instance.")
    timestamp: datetime = Field(..., description="Timestamp of when the deployment succeeded.")
    source_type: SourceType = Field(..., description="The type of the source code (local or git).")
    source_identifier: str = Field(..., description="The identifier for the source (commit SHA for git, archive path for local).")

class BalanceRead(BaseModel):
    month_to_date_balance: str
    account_balance: str
    month_to_date_usage: str
    generated_at: str
    error: str | None = None

class DropletCostRead(BaseModel):
    id: int
    name: str
    ip_address: str
    status: str
    size_slug: str
    monthly_price: float

class ProjectRead(BaseModel):
    id: int
    name: str
    ip_address: str | None = None
    status: str
    region: str
    size_slug: str
    estimated_monthly_cost: float | None = None
    created_at: datetime


