"""DLNIRSP control of FITS key names and values."""

from enum import StrEnum


class DlnirspMetadataKey(StrEnum):
    """Controlled list of names for FITS metadata header keys."""

    crpix_1 = "CRPIX1"
    crpix_2 = "CRPIX2"
    modulator_spin_mode = "DLMOD"
    camera_readout_mode = "DLCAMSMD"
    num_frames_in_ramp = "DLCAMNS"
    current_frame_in_ramp = "DLCAMCUR"
    arm_id = "DLARMID"
    camera_sample_sequence = "DLCAMSSQ"
    polarimeter_mode = "DLPOLMD"
    number_of_modulator_states = "DLNUMST"
    modulator_state = "DLSTNUM"
    num_mosaic_repeats = "DLMOSNRP"
    mosaic_num = "DLCURMOS"
    num_X_tiles = "DLNSSTPX"
    X_tile_num = "DLCSTPX"
    num_Y_tiles = "DLNSSTPY"
    Y_tile_num = "DLCSTPY"
    num_dither_steps = "DLDMODE"
    dither_step = "DLCURSTP"
    arm_position_mm = "DLARMPS"
    grating_position_deg = "DLGRTAN"
    grating_constant_inverse_mm = "DLGRTCN"
