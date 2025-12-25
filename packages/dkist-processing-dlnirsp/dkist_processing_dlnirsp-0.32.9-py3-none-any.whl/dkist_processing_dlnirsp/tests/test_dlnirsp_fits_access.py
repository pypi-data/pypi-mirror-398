import pytest
from astropy.io import fits
from dkist_header_validator.translator import translate_spec122_to_spec214_l0

from dkist_processing_dlnirsp.models.fits_access import DlnirspMetadataKey
from dkist_processing_dlnirsp.parsers.dlnirsp_l0_fits_access import DlnirspL0FitsAccess
from dkist_processing_dlnirsp.parsers.dlnirsp_l0_fits_access import DlnirspRampFitsAccess
from dkist_processing_dlnirsp.parsers.dlnirsp_l1_fits_acess import DlnirspL1FitsAccess
from dkist_processing_dlnirsp.tests.conftest import DlnirspHeaders


@pytest.fixture
def ramp_header(arm_id):
    dataset = DlnirspHeaders(
        dataset_shape=(2, 2, 2), array_shape=(1, 2, 2), time_delta=1.0, arm_id=arm_id
    )
    translated_header = fits.Header(translate_spec122_to_spec214_l0(dataset.header()))
    return translated_header


@pytest.fixture
def dither_header(dither_mode_on, dither_step):
    dataset = DlnirspHeaders(
        dataset_shape=(2, 2, 2),
        array_shape=(1, 2, 2),
        time_delta=1.0,
        dither_mode_on=dither_mode_on,
        dither_step=dither_step,
    )
    translated_header = fits.Header(translate_spec122_to_spec214_l0(dataset.header()))
    return translated_header


@pytest.mark.parametrize(
    "arm_id", [pytest.param("JBand"), pytest.param("HBand"), pytest.param("VIS")]
)
def test_dlnirsp_ramp_fits_access(ramp_header, arm_id):
    """
    Given: A header that may or may not contain IR camera-specific header keys
    When: Parsing the header with `DlnirspRampFitsAccess`
    Then: If the data are IR then the header values are parsed, and if the data are VIS then dummy values are returned
          for the IR-only keys.
    """
    fits_obj = DlnirspRampFitsAccess.from_header(ramp_header)

    assert fits_obj.arm_id == arm_id
    if arm_id == "VIS":
        assert fits_obj.camera_readout_mode == "DEFAULT_VISIBLE_CAMERA"
        assert fits_obj.num_frames_in_ramp == -99
        assert fits_obj.current_frame_in_ramp == -88

    else:
        assert fits_obj.camera_readout_mode == ramp_header[DlnirspMetadataKey.camera_readout_mode]
        assert fits_obj.num_frames_in_ramp == ramp_header[DlnirspMetadataKey.num_frames_in_ramp]
        assert (
            fits_obj.current_frame_in_ramp == ramp_header[DlnirspMetadataKey.current_frame_in_ramp]
        )


@pytest.mark.parametrize(
    "dither_mode_on",
    [pytest.param(False, id="dither_mode_off"), pytest.param(True, id="dither_mode_on")],
)
@pytest.mark.parametrize(
    "dither_step",
    [pytest.param(True, id="dither_step_true"), pytest.param(False, id="dither_step_false")],
)
def test_dlnirsp_l0_fits_access(dither_header, dither_mode_on, dither_step):
    """
    Given: A header with dither-related keys
    When: Parsing the header with `DlnirspL0FitsAccess`
    Then: The parsed properties are correct and `dither_step` is always 0 if `num_dither_steps` is 1.
    """
    fits_obj = DlnirspL0FitsAccess.from_header(dither_header)

    assert fits_obj.num_dither_steps is dither_mode_on + 1
    if not dither_mode_on:
        assert fits_obj.dither_step is 0
    else:
        assert fits_obj.dither_step == int(dither_step)


@pytest.mark.parametrize("arm_id", [pytest.param("VIS", id="vis_arm")])
def test_metadata_keys_in_access_bases(ramp_header, arm_id):
    """
    Given: the set of metadata key names in DlnirspMetadataKey
    When: the Dlnirsp FITS access classes define a set of new attributes
    Then: the sets are the same and the attributes have the correct values
    """
    dlnirsp_metadata_key_names = {dmk.name for dmk in DlnirspMetadataKey}
    all_dlnirsp_fits_access_attrs = set()
    for access_class in [DlnirspRampFitsAccess, DlnirspL0FitsAccess, DlnirspL1FitsAccess]:
        fits_obj = access_class.from_header(ramp_header)
        dlnirsp_instance_attrs = set(vars(fits_obj).keys())
        parent_class = access_class.mro()[1]
        parent_fits_obj = parent_class.from_header(ramp_header)
        parent_instance_attrs = set(vars(parent_fits_obj).keys())
        dlnirsp_fits_access_attrs = dlnirsp_instance_attrs - parent_instance_attrs
        for attr in dlnirsp_fits_access_attrs:
            match attr:
                case "num_frames_in_ramp":
                    assert getattr(fits_obj, attr) == fits_obj.header.get(
                        DlnirspMetadataKey[attr], -99
                    )
                case "current_frame_in_ramp":
                    assert getattr(fits_obj, attr) == fits_obj.header.get(
                        DlnirspMetadataKey[attr], -88
                    )
                case "camera_sample_sequence":
                    assert getattr(fits_obj, attr) == fits_obj.header.get(
                        DlnirspMetadataKey[attr], "VISIBLE_CAMERA_SEQUENCE"
                    )
                case "camera_readout_mode":
                    assert getattr(fits_obj, attr) == fits_obj.header.get(
                        DlnirspMetadataKey[attr], "DEFAULT_VISIBLE_CAMERA"
                    )
                case "num_dither_steps":
                    assert (
                        getattr(fits_obj, attr)
                        == int(fits_obj.header[DlnirspMetadataKey[attr]]) + 1
                    )
                case "dither_step":
                    assert getattr(fits_obj, attr) == int(
                        fits_obj.header.get(DlnirspMetadataKey[attr], False)
                    )
                case _:
                    assert getattr(fits_obj, attr) == fits_obj.header[DlnirspMetadataKey[attr]]
        all_dlnirsp_fits_access_attrs |= dlnirsp_fits_access_attrs
    assert dlnirsp_metadata_key_names == all_dlnirsp_fits_access_attrs
