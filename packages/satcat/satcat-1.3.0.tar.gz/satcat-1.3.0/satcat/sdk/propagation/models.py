from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field

from satcat.sdk.models import Model

DEFAULT_PROPAGATION_DURATION_S = 86400 * 5
DEFAULT_PROPAGATION_TIMESTEP_S = 60

if TYPE_CHECKING:
    from satcat.sdk.client import Client


class PropagationConfiguration(Model):
    start_time: Optional[datetime] = Field(
        None, description="The start time of the propagation interval (UTC)."
    )
    end_time: Optional[datetime] = Field(
        None,
        description=(
            "The end time of the propagation interval (UTC). Use either this field or"
            " target_duration"
        ),
    )
    target_duration: Optional[float] = Field(
        None,
        description=(
            "The duration of the propagation interval in seconds. Use either this field"
            " or end_time"
        ),
    )
    timestep: float = Field(
        DEFAULT_PROPAGATION_TIMESTEP_S,
        description="The step size between points of the propagation in seconds",
    )
    purpose: str = "MANUAL"
    infer_interval_from_screening: bool = Field(
        True,
        description="Whether to automatically update the interval of the propagation (otherwise configured by start_time, end_time, and target_duration) to automatically match the usable time interval of the available counterpart screening data when the Propagation is attached as a primary or secondary to a Screening."
    )

    class Config:
        allow_population_by_field_name = True


class Propagation(PropagationConfiguration):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    ephemeris_id: Optional[str] = None
