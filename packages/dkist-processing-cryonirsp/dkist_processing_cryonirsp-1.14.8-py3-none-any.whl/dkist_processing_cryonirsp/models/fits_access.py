"""CryoNIRSP control of FITS key names and values."""

from enum import StrEnum
from enum import unique


@unique
class CryonirspMetadataKey(StrEnum):
    """Controlled list of names for FITS metadata header keys."""

    camera_readout_mode = "CNCAMMD"
    curr_frame_in_ramp = "CNCNDR"
    num_frames_in_ramp = "CNNNDR"
    arm_id = "CNARMID"
    roi_1_origin_x = "HWROI1OX"
    roi_1_origin_y = "HWROI1OY"
    roi_1_size_x = "HWROI1SX"
    roi_1_size_y = "HWROI1SY"
    filter_name = "CNFILTNP"
    number_of_modulator_states = "CNMODNST"
    modulator_state = "CNMODCST"
    scan_step = "CNCURSCN"
    num_scan_steps = "CNNUMSCN"
    num_cn1_scan_steps = "CNP1DNSP"
    num_cn2_scan_steps = "CNP2DNSP"
    cn2_step_size = "CNP2DSS"
    cn1_scan_step = "CNP1DCUR"
    meas_num = "CNCMEAS"
    num_meas = "CNNMEAS"
    sub_repeat_num = "CNCSREP"
    num_sub_repeats = "CNSUBREP"
    modulator_spin_mode = "CNSPINMD"
    axis_1_type = "CTYPE1"
    axis_2_type = "CTYPE2"
    axis_3_type = "CTYPE3"
    grating_position_deg = "CNGRTPOS"
    grating_littrow_angle_deg = "CNGRTLAT"
    grating_constant = "CNGRTCON"
    center_wavelength = "CNCENWAV"
    slit_width = "CNSLITW"
