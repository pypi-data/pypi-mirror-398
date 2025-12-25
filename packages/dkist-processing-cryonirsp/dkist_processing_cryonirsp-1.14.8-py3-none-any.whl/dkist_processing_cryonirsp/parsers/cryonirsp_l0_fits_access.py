"""CryoNIRSP FITS access for L0 data."""

import numpy as np
from astropy.io import fits
from dkist_processing_common.parsers.l0_fits_access import L0FitsAccess

from dkist_processing_cryonirsp.models.exposure_conditions import CRYO_EXP_TIME_ROUND_DIGITS
from dkist_processing_cryonirsp.models.exposure_conditions import ExposureConditions
from dkist_processing_cryonirsp.models.fits_access import CryonirspMetadataKey


class CryonirspRampFitsAccess(L0FitsAccess):
    """
    Class to provide easy access to L0 headers for non-linearized (raw) files.

    i.e. instead of <CryonirspL0FitsAccess>.header['key'] this class lets us use <CryonirspL0FitsAccess>.key instead

    Parameters
    ----------
    hdu :
        Fits L0 header object

    name : str
        The name of the file that was loaded into this FitsAccess object

    auto_squeeze : bool
        When set to True, dimensions of length 1 will be removed from the array
    """

    def __init__(
        self,
        hdu: fits.ImageHDU | fits.PrimaryHDU | fits.CompImageHDU,
        name: str | None = None,
        auto_squeeze: bool = True,
    ):
        super().__init__(hdu=hdu, name=name, auto_squeeze=auto_squeeze)

        self.camera_readout_mode = self.header[CryonirspMetadataKey.camera_readout_mode]
        self.curr_frame_in_ramp: int = self.header[CryonirspMetadataKey.curr_frame_in_ramp]
        self.num_frames_in_ramp: int = self.header[CryonirspMetadataKey.num_frames_in_ramp]
        self.arm_id: str = self.header[CryonirspMetadataKey.arm_id]
        self.filter_name = self.header[CryonirspMetadataKey.filter_name].upper()
        self.roi_1_origin_x = self.header[CryonirspMetadataKey.roi_1_origin_x]
        self.roi_1_origin_y = self.header[CryonirspMetadataKey.roi_1_origin_y]
        self.roi_1_size_x = self.header[CryonirspMetadataKey.roi_1_size_x]
        self.roi_1_size_y = self.header[CryonirspMetadataKey.roi_1_size_y]


class CryonirspL0FitsAccess(L0FitsAccess):
    """
    Class to provide easy access to L0 headers for linearized (ready for processing) files.

    i.e. instead of <CryonirspL0FitsAccess>.header['key'] this class lets us use <CryonirspL0FitsAccess>.key instead

    Parameters
    ----------
    hdu :
        Fits L0 header object

    name : str
        The name of the file that was loaded into this FitsAccess object

    auto_squeeze : bool
        When set to True, dimensions of length 1 will be removed from the array
    """

    def __init__(
        self,
        hdu: fits.ImageHDU | fits.PrimaryHDU | fits.CompImageHDU,
        name: str | None = None,
        auto_squeeze: bool = True,
    ):
        super().__init__(hdu=hdu, name=name, auto_squeeze=auto_squeeze)

        self.arm_id: str = self.header[CryonirspMetadataKey.arm_id]
        self.number_of_modulator_states: int = self.header[
            CryonirspMetadataKey.number_of_modulator_states
        ]
        self.modulator_state: int = self.header[CryonirspMetadataKey.modulator_state]
        self.scan_step: int = self.header[CryonirspMetadataKey.scan_step]
        self.num_scan_steps: int = self.header[CryonirspMetadataKey.num_scan_steps]
        self.num_cn1_scan_steps: int = self.header[CryonirspMetadataKey.num_cn1_scan_steps]
        self.num_cn2_scan_steps: int = self.header[CryonirspMetadataKey.num_cn2_scan_steps]
        self.cn2_step_size: float = self.header[CryonirspMetadataKey.cn2_step_size]
        self.meas_num: int = self.header[CryonirspMetadataKey.meas_num]
        self.num_meas: int = self.header[CryonirspMetadataKey.num_meas]
        self.sub_repeat_num = self.header[CryonirspMetadataKey.sub_repeat_num]
        self.num_sub_repeats: int = self.header[CryonirspMetadataKey.num_sub_repeats]
        self.modulator_spin_mode: str = self.header[CryonirspMetadataKey.modulator_spin_mode]
        self.axis_1_type: str = self.header[CryonirspMetadataKey.axis_1_type]
        self.axis_2_type: str = self.header[CryonirspMetadataKey.axis_2_type]
        self.axis_3_type: str = self.header[CryonirspMetadataKey.axis_3_type]
        self.grating_position_deg: float = self.header[CryonirspMetadataKey.grating_position_deg]
        self.grating_littrow_angle_deg: float = self.header[
            CryonirspMetadataKey.grating_littrow_angle_deg
        ]
        self.grating_constant: float = self.header[CryonirspMetadataKey.grating_constant]
        self.filter_name = self.header[CryonirspMetadataKey.filter_name.value].upper()
        # The ExposureConditions are a combination of the exposure time and the OD filter name:
        self.exposure_conditions = ExposureConditions(
            round(self.fpa_exposure_time_ms, CRYO_EXP_TIME_ROUND_DIGITS), self.filter_name
        )
        self.center_wavelength = self.header[CryonirspMetadataKey.center_wavelength]
        self.slit_width = self.header[CryonirspMetadataKey.slit_width]
        # Convert the inner loop step number from float to int:
        self.cn1_scan_step = int(self.header[CryonirspMetadataKey.cn1_scan_step])


class CryonirspLinearizedFitsAccess(CryonirspL0FitsAccess):
    """
    Class to access to linearized CryoNIRSP data.

    Flip the dispersion axis of the SP arm.
    Cryo's wavelength decreases from left to right, so we flip it here to match the other instruments.

    Parameters
    ----------
    hdu :
        Fits L0 header object

    name : str
        The name of the file that was loaded into this FitsAccess object

    auto_squeeze : bool
        When set to True, dimensions of length 1 will be removed from the array
    """

    @property
    def data(self):
        """Override parent method to flip the SP arm array."""
        parent_data = super().data
        if self.arm_id == "SP":
            return np.flip(parent_data, 1)
        return parent_data

    @data.setter
    def data(self, value: np.array):
        """Override parent setter method to unflip the SP arm array."""
        if self.arm_id == "SP":
            value = np.flip(value, 1)
        super(CryonirspL0FitsAccess, type(self)).data.__set__(self, value)
