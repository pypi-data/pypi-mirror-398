from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from satcat.sdk.models import Model
from satcat.sdk.propagation.models import Propagation

if TYPE_CHECKING:
    from satcat.sdk.client import Client


class EphemerisType(str, Enum):
    ON_ORBIT = "ON_ORBIT"
    LAUNCH = "LAUNCH"


class ScreeningType(str, Enum):
    ON_ORBIT = "ON_ORBIT"
    LAUNCH = "LAUNCH"


class EphemerisDesignation(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    PREDICTIVE = "PREDICTIVE"
    DEFINITIVE = "DEFINITIVE"
    THEORETICAL = "THEORETICAL"


class EphemerisContext(str, Enum):
    ROUTINE = "ROUTINE"
    MAINTENANCE = "MAINTENANCE"
    COLA = "COLA"
    DECAY = "DECAY"
    NOVEL = "NOVEL"


class EphemerisGroup(str, Enum):
    OPERATOR_REPOSITORY = "OPERATOR_REPOSITORY"


class CoverageLevel(str, Enum):
    NO_OVERLAP = "NO_OVERLAP"
    PARTIAL = "PARTIAL"
    FULL = "FULL"


class HardBodyShape(str, Enum):
    SQUARE = "SQUARE"
    CIRCLE = "CIRCLE"


class EphemerisSource(str, Enum):
    CATALOG = "CATALOG"
    SPACE_TRACK_PUBLIC = "SPACE_TRACK_PUBLIC"
    PATHFINDER_API = "PATHFINDER_API"
    SATCAT_API = "SATCAT_API"
    USER_SCREENER = "USER_SCREENER"
    TERTIARY_SCREENER = "TERTIARY_SCREENER"
    PATHFINDER_AUTO_THIRDPARTY = "PATHFINDER_AUTO_THIRDPARTY"
    KAYHAN_INTERNAL_PROCESS = "KAYHAN_INTERNAL_PROCESS"
    STARLINK_API_PUBLIC = "STARLINK_API_PUBLIC"


class ExternalCatalog(str, Enum):
    STARLINK = "STARLINK"


class Catalog(Model):
    id: str
    catalog_type: Optional[str] = None
    archived: Optional[bool] = None
    ready: Optional[bool] = None
    epoch: Optional[datetime] = None
    filename: Optional[str] = None


class RSO(Model):
    norad_id: int
    object_name: Optional[str]
    object_type: Optional[str]


class Ephemeris(Model):
    # ephemeris_type: EphemerisType = EphemerisType.ON_ORBIT
    ephemeris_source: Optional[Union[EphemerisSource, str]] = None
    current_operational: Optional[bool] = None
    id: Optional[str] = None
    has_covariance: Optional[bool] = None
    apogee_km: Optional[float] = None
    perigee_km: Optional[float] = None
    archived: Optional[bool] = None
    user_id: Optional[str] = None
    # catalog: Optional[Catalog] = None
    norad_id: Optional[int] = None
    solution_time: Optional[datetime] = None
    # rso: Optional[RSO] = None
    hbr_m: Optional[float] = None
    filename: Optional[str] = None
    usable_time_start: Optional[datetime] = None
    usable_time_end: Optional[datetime] = None
    context: Optional[EphemerisContext] = None
    designation: Optional[EphemerisDesignation] = None
    comments: Optional[str] = None
    data_format: Optional[str] = None
    launch_time: Optional[datetime] = None
    covariance_corrected: Optional[bool] = None
    source_ephemeris_id: Optional[str] = None


class Screenable(Model):
    ephemeris_id: Optional[str] = None
    catalog_id: Optional[str] = None
    propagation_id: Optional[str] = None
    ephemeris: Optional[Ephemeris] = None
    catalog: Optional[Catalog] = None
    propagation: Optional[Propagation] = None
    norad_id: Optional[int] = None
    usable_time_start: Optional[datetime] = None
    usable_time_end: Optional[datetime] = None
    coverage_level: Optional[CoverageLevel] = None
    coverage_ratio: Optional[float] = None
    ephemeris_group: Optional[EphemerisGroup] = None
    external_catalog: Optional[ExternalCatalog] = None


class ScreeningConfiguration(Model):
    threshold_radius_km: float = 15.0
    threshold_radius_active_km: Optional[float] = None
    threshold_radius_manned_km: Optional[float] = None
    threshold_radius_debris_km: Optional[float] = None
    default_secondary_hbr_m: float = 5.0
    propagation_start_time: Optional[datetime] = None
    # propagation_duration: Optional[float] = None
    # propagation_timestep: Optional[float] = None
    auto_archive: bool = False
    include_primary_vs_primary: bool = False
    screening_type: ScreeningType = ScreeningType.ON_ORBIT
    launch_window_start: Optional[datetime] = None
    launch_window_end: Optional[datetime] = None
    launch_window_cadence_s: Optional[float] = None
    title: Optional[str] = "Screening"
    notes: Optional[str] = "Created using Satcat SDK"
    hard_body_shape: HardBodyShape = HardBodyShape.SQUARE


class Conjunction(Model):
    cdm_id: Optional[int] = None
    tca: datetime
    miss_distance_km: float
    originator: Optional[str] = None

    launch_time: Optional[datetime] = None
    id: Optional[str] = None
    collision_probability: Optional[float] = None
    collision_probability_method: Optional[str] = None
    created_at: Optional[datetime] = None
    primary: Optional[Ephemeris] = None
    secondary: Optional[Ephemeris] = None
    key_number: int

    @property
    def key(self) -> str:
        originator_prefix = "X"
        if self.originator:
            if self.originator.upper() in {"JSPOC", "CSPOC"}:
                originator_prefix = "S"
            elif self.originator.upper() == "KAYHAN":
                originator_prefix = "K"
        return f"CDM-{originator_prefix}{self.key_number}"


class Screening(ScreeningConfiguration):
    id: str
    status: Optional[str] = None
    screening_type: Optional[ScreeningType] = ScreeningType.ON_ORBIT
    created_at: Optional[datetime] = None
    primaries_count: Optional[int] = None
    secondaries_count: Optional[int] = None
    conjunctions_count: Optional[int] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    percent_complete: Optional[float] = None
    coverage_level: Optional[CoverageLevel] = None
    coverage_ratio: Optional[float] = None
    primary_rsos_preview: Optional[List[RSO]] = None

    @property
    def primary_ids_preview(self) -> List[int]:
        return [r.norad_id for r in self.primary_rsos_preview]
