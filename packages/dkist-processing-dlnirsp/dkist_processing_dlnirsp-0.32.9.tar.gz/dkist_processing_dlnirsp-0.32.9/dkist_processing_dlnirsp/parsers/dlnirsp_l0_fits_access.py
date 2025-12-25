"""DLNIRSP FitsAccess classes for raw and linearized data."""

from astropy.io import fits
from dkist_processing_common.parsers.l0_fits_access import L0FitsAccess

from dkist_processing_dlnirsp.models.fits_access import DlnirspMetadataKey


class DlnirspRampFitsAccess(L0FitsAccess):
    """
    Class to provide easy access to L0 headers for non-linearized (raw) DLNIRSP data.

    i.e. instead of <DlnirspL0FitsAccess>.header['weird_key'] this class lets us use <DlnirspL0FitsAccess>.nice_key instead

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

        self.modulator_spin_mode: str = self.header[DlnirspMetadataKey.modulator_spin_mode]
        self.camera_readout_mode: str = self.header.get(
            DlnirspMetadataKey.camera_readout_mode, "DEFAULT_VISIBLE_CAMERA"
        )
        self.num_frames_in_ramp: int = self.header.get(DlnirspMetadataKey.num_frames_in_ramp, -99)
        self.current_frame_in_ramp: int = self.header.get(
            DlnirspMetadataKey.current_frame_in_ramp, -88
        )
        self.arm_id: str = self.header[DlnirspMetadataKey.arm_id]
        self.camera_sample_sequence: str = self.header.get(
            DlnirspMetadataKey.camera_sample_sequence, "VISIBLE_CAMERA_SEQUENCE"
        )


class DlnirspL0FitsAccess(L0FitsAccess):
    """
    Class to provide easy access to L0 headers for linearized (ready for processing) DLNIRSP data.

    i.e. instead of <DlnirspL0FitsAccess>.header['weird_key'] this class lets us use <DlnirspL0FitsAccess>.nice_key instead

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

        self.crpix_1: float = self.header[DlnirspMetadataKey.crpix_1]
        self.crpix_2: float = self.header[DlnirspMetadataKey.crpix_2]
        self.arm_id: str = self.header[DlnirspMetadataKey.arm_id]
        self.polarimeter_mode: str = self.header[DlnirspMetadataKey.polarimeter_mode]
        self.number_of_modulator_states: int = self.header[
            DlnirspMetadataKey.number_of_modulator_states
        ]
        self.modulator_state: int = self.header[DlnirspMetadataKey.modulator_state]
        self.num_mosaic_repeats: int = self.header[DlnirspMetadataKey.num_mosaic_repeats]
        self.mosaic_num: int = self.header[DlnirspMetadataKey.mosaic_num]
        self.num_X_tiles: int = self.header[DlnirspMetadataKey.num_X_tiles]
        self.X_tile_num: int = self.header[DlnirspMetadataKey.X_tile_num]
        self.num_Y_tiles: int = self.header[DlnirspMetadataKey.num_Y_tiles]
        self.Y_tile_num: int = self.header[DlnirspMetadataKey.Y_tile_num]
        # DLDMODE is a bool in the header; the number of dither steps is either 1 or 2, corresponding to dither
        # mode being True or False, respectively
        self.num_dither_steps: int = int(self.header[DlnirspMetadataKey.num_dither_steps]) + 1
        # Same with DLCURSTP. We'll index the dither loop at 0 so `False` is the first step and `True` is the second
        # Use `get` because this key only exists if DLDMODE is `True`
        self.dither_step: int = int(self.header.get(DlnirspMetadataKey.dither_step, False))
        self.arm_position_mm: float = self.header[DlnirspMetadataKey.arm_position_mm]
        self.grating_position_deg: float = self.header[DlnirspMetadataKey.grating_position_deg]
        self.grating_constant_inverse_mm: float = self.header[
            DlnirspMetadataKey.grating_constant_inverse_mm
        ]
