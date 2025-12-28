from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from satcat.sdk.models import Model
from satcat.sdk.screening.models import RSO


class RSOMetadataModel(Model):
    country: Optional[str] = None


class RSODetailed(RSO):
    id: str
    interational_id: Optional[str] = None
    rso_metadata: Optional[RSOMetadataModel] = None


class SpacecraftConjunctionState(Model):
    comment_screening_data_source: Optional[str] = None
    ephemeris_name: Optional[str] = None
    covariance_method: Optional[str] = None
    ref_frame: Optional[str] = None
    intrack_thrust: Optional[str] = None
    comment_covariance_scale_factor: Optional[str] = None
    comment_exclusion_volume_radius: Optional[str] = None
    hbr_m: Optional[str] = None
    time_lastob_start: Optional[datetime] = None
    time_lastob_end: Optional[datetime] = None
    x_km: Optional[float] = None
    y_km: Optional[float] = None
    z_km: Optional[float] = None
    x_dot_km: Optional[float] = None
    y_dot_km: Optional[float] = None
    z_dot_km: Optional[float] = None
    cr_r: Optional[float] = None
    ct_r: Optional[float] = None
    ct_t: Optional[float] = None
    cn_r: Optional[float] = None
    cn_t: Optional[float] = None
    cn_n: Optional[float] = None
    crdot_r: Optional[float] = None
    crdot_t: Optional[float] = None
    crdot_n: Optional[float] = None
    crdot_rdot: Optional[float] = None
    ctdot_r: Optional[float] = None
    ctdot_t: Optional[float] = None
    ctdot_n: Optional[float] = None
    ctdot_rdot: Optional[float] = None
    ctdot_tdot: Optional[float] = None
    cndot_r: Optional[float] = None
    cndot_t: Optional[float] = None
    cndot_n: Optional[float] = None
    cndot_rdot: Optional[float] = None
    cndot_tdot: Optional[float] = None
    cndot_ndot: Optional[float] = None
    cdrg_r: Optional[float] = None
    cdrg_t: Optional[float] = None
    cdrg_n: Optional[float] = None
    cdrg_rdot: Optional[float] = None
    cdrg_tdot: Optional[float] = None
    cdrg_ndot: Optional[float] = None
    cdrg_drg: Optional[float] = None
    csrp_r: Optional[float] = None
    csrp_t: Optional[float] = None
    csrp_n: Optional[float] = None
    csrp_rdot: Optional[float] = None
    csrp_tdot: Optional[float] = None
    csrp_ndot: Optional[float] = None
    csrp_drg: Optional[float] = None
    csrp_srp: Optional[float] = None
    ephemeris_id: Optional[UUID] = None
    screening_id: Optional[UUID] = None
    altitude_km: Optional[float] = None


class ConjunctionMinimal(Model):
    cdm_id: Optional[int] = None
    tca: datetime
    miss_distance_km: float
    event_id: str
    originator: Optional[str] = None

    collision_probability: Optional[float] = None
    collision_probability_method: Optional[str] = None
    original_collision_probability: Optional[float] = None
    original_collision_probability_method: Optional[str] = None
    primary: Optional[RSO] = None
    secondary: Optional[RSO] = None
    creation_date: Optional[datetime] = None
    key: Optional[str] = None


class ConjunctionDetailed(ConjunctionMinimal):
    id: str
    event_id: str
    created_at: datetime
    updated_at: datetime
    designation: Optional[str] = None
    key_number: Optional[int] = None
    relative_velocity_mag_km_s: Optional[float] = None
    relative_position_r_km: Optional[float] = None
    relative_position_i_km: Optional[float] = None
    relative_position_c_km: Optional[float] = None
    relative_velocity_r_km_s: Optional[float] = None
    relative_velocity_i_km_s: Optional[float] = None
    relative_velocity_c_km_s: Optional[float] = None
    frisbee_collision_probability: Optional[float] = None
    frisbee_collision_probability_method: Optional[str] = None
    angle_of_approach: Optional[float] = None
    mahalanobis_distance: Optional[float] = None
    relative_miss_sig_m: Optional[float] = None
    relative_sig_r_u_m: Optional[float] = None
    relative_sig_it_u_m: Optional[float] = None
    relative_sig_ct_u_m: Optional[float] = None
    is_intra_org: Optional[bool] = None

    primary: Optional[RSODetailed] = None
    secondary: Optional[RSODetailed] = None

    primary_state: Optional[SpacecraftConjunctionState] = None
    secondary_state: Optional[SpacecraftConjunctionState] = None


class Event(Model):
    id: str
    key: str
    created_at: datetime
    updated_at: datetime
    tca_range_start: datetime
    tca_range_end: datetime
    default_cdm: Optional[ConjunctionMinimal] = None


class PCRemediationMethod(str, Enum):
    FRISBEE = "frisbee"
    HALL = "hall"
    MULTISTEP = "multistep"
