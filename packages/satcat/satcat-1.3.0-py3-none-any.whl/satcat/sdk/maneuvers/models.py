from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Union, Literal
from typing_extensions import Annotated
from uuid import UUID
try:
    from pydantic.v1 import Extra, Field
except ImportError:
    from pydantic import Extra, Field


from satcat.sdk.models import Model

if TYPE_CHECKING:
    from satcat.sdk.client import Client

class ManeuverProject(Model):
    id: UUID
    created_at: Optional[datetime] = None
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    name: Optional[str] = None
    automatically_generated: Optional[bool] = None
    project_type: Optional[str] = None

class ColaSettingsBase(Model, extra=Extra.allow):
    ...

class DVAllowedFrame(str, Enum):
    RIC = "RIC"


class HBRSource(str, Enum):
    RECOMMENDED = "recommended"
    CUSTOM = "custom"
    CDM = "cdm"
    CDM_ORIGINAL = "cdm_original"
    ORGANIZATION_OWNED = "organization_owned"
    SPACE_TRACK = "space-track"
    CARA = "cara"
    BASE = "base"


class SimpleManeuverDesignerRSOAttributes(ColaSettingsBase):
    mass_kg: Optional[Annotated[float, Field(ge=0)]] = None
    area_drag_m2: Optional[Annotated[float, Field(ge=0)]] = None
    area_rad_m2: Optional[Annotated[float, Field(ge=0)]] = None
    coeff_drag:Optional[Annotated[float, Field(ge=0)]] = None
    coeff_rad: Optional[Annotated[float, Field(ge=0)]] = None
    hbr_m: Optional[Annotated[float, Field(gt=0)]] = None
    hbr_source: HBRSource = HBRSource.CDM

class SimpleManeuverDesignerSecondaryRSOAttributes(ColaSettingsBase):
    hbr_m: Optional[Annotated[float, Field(gt=0)]] = None
    hbr_source: HBRSource = "cdm"


class EphemerisDataSource(ColaSettingsBase):
    source_type: Literal["EPHEMERIS"] = "EPHEMERIS"
    ephemeris_id: str


class CDMDataSource(ColaSettingsBase):
    source_type: Literal["CDM"] = "CDM"

SimpleManeuverDesignerDataSource = Annotated[
    Union[CDMDataSource, EphemerisDataSource],
    Field(
        discriminator="source_type",
        description="Data source for the primary RSO state.",
    ),
]


class GatesManeuverExecutionUncertainty(ColaSettingsBase):
    type: Literal["GATES"] = "GATES"
    magnitude_fixed_error_m_s: Annotated[float, Field(ge=0)] = 0.0
    magnitude_proportional_error_frac: Annotated[float, Field(ge=0, le=1)] = 0.0
    pointing_fixed_error_m_s: Annotated[float, Field(ge=0)] = 0.0
    pointing_angle_error_rad: Annotated[float, Field(ge=0, le=1)] = 0.0


class ColaManeuverVariantSettings(ColaSettingsBase):
    runner: Literal["sensitivity"] = "sensitivity" 
    aggregate_tertiary_cdms: bool = True
    man_ignition_time_start_tca_minus_hours: Annotated[int, Field(le=24 * 5, ge=0)] = 72
    man_ignition_time_end_tca_minus_hours: Annotated[int, Field(le=24 * 5, ge=0)] = 0

    tradespace_ignition_times_per_period: Annotated[int, Field(le=8, ge=1)] = 2

    man_dv_direction_x: float = 0.0
    man_dv_direction_y: float = 1.0
    man_dv_direction_z: float = 0.0
    man_dv_frame: DVAllowedFrame = DVAllowedFrame.RIC

    man_dv_mag_min_m_s: float = -0.1
    man_dv_mag_max_m_s: float = 0.1

    man_execution_uncertainty: Optional[
        GatesManeuverExecutionUncertainty
    ] = None

    primary_propagation_attributes: SimpleManeuverDesignerRSOAttributes = Field(
        default_factory=SimpleManeuverDesignerRSOAttributes
    )

    secondary_propagation_attributes: SimpleManeuverDesignerSecondaryRSOAttributes = (
        Field(default_factory=SimpleManeuverDesignerSecondaryRSOAttributes)
    )

    primary_data_source: SimpleManeuverDesignerDataSource = CDMDataSource()

class SimpleManeuverPlanParameters(ColaSettingsBase):
    man_dv_mag_m_s: float
    man_dv_direction_x: float
    man_dv_direction_y: float
    man_dv_direction_z: float
    man_dv_frame: DVAllowedFrame


class SimpleManeuverTradespacePoint(SimpleManeuverPlanParameters):
    pc: Optional[float] = None
    miss_km: float
    mahalanobis_distance: Optional[float] = None

    agg_pc: Optional[float] = None
    agg_min_miss_km: Optional[float] = None

    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float


class SimpleManeuverTradespaceRow(ColaSettingsBase):
    time_utc: str
    points: List[SimpleManeuverTradespacePoint]

class ColaManeuverVariantConfiguration(Model):
    name: Optional[str] = None
    original_conjunction_id: Optional[UUID] = None
    settings_data: Optional[ColaManeuverVariantSettings] = None


class ColaManeuverVariant(ColaManeuverVariantConfiguration):
    id: UUID
    created_at: Optional[datetime] = None
    project_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    status: Optional[str] = None


class ColaManeuverVariantWithTradespace(ColaManeuverVariant):
    tradespace_data: Optional[List[SimpleManeuverTradespaceRow]] = None

class TimestampedSimpleManeuverPlanParameters(SimpleManeuverPlanParameters):
    time_utc: str

class ColaManeuverHifiPlan(ColaSettingsBase):
    variant_id: Optional[str] = None
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    ephemeris_id: Optional[str] = None
    conjunction_id: Optional[str] = None
    name: Optional[str] = None
    parameters_data: Optional[TimestampedSimpleManeuverPlanParameters] = None

    opm_file_content: Optional[str] = None
