import pytest
from dkist_header_validator.translator import translate_spec122_to_spec214_l0

from dkist_processing_cryonirsp.models.fits_access import CryonirspMetadataKey
from dkist_processing_cryonirsp.parsers.cryonirsp_l0_fits_access import CryonirspL0FitsAccess
from dkist_processing_cryonirsp.parsers.cryonirsp_l0_fits_access import CryonirspRampFitsAccess
from dkist_processing_cryonirsp.parsers.cryonirsp_l1_fits_access import CryonirspL1FitsAccess
from dkist_processing_cryonirsp.tests.header_models import Cryonirsp122ObserveFrames


@pytest.fixture(scope="session")
def complete_header():
    dataset = Cryonirsp122ObserveFrames(array_shape=(1, 2, 2))
    header = [translate_spec122_to_spec214_l0(d.header()) for d in dataset]
    return header


def test_metadata_keys_in_access_bases(complete_header):
    """
    Given: the set of metadata key names in CryonirspMetadataKey
    When: the Cryo FITS access classes define a set of new attributes
    Then: the sets are the same and the attributes have the correct values
    """
    cryo_metadata_key_names = {cmk.name for cmk in CryonirspMetadataKey}
    all_cryo_fits_access_attrs = set()
    for access_class in [CryonirspRampFitsAccess, CryonirspL0FitsAccess, CryonirspL1FitsAccess]:
        fits_obj = access_class.from_header(complete_header[0])
        cryo_instance_attrs = set(vars(fits_obj).keys())
        parent_class = access_class.mro()[1]
        parent_fits_obj = parent_class.from_header(complete_header[0])
        parent_instance_attrs = set(vars(parent_fits_obj).keys())
        cryo_fits_access_attrs = cryo_instance_attrs - parent_instance_attrs
        # exposure_conditions is created from multiple header keys, so it is not in CryonirspMetadataKey:
        cryo_fits_access_attrs -= {"exposure_conditions"}
        for attr in cryo_fits_access_attrs:
            match attr:
                case "cn1_scan_step":
                    assert getattr(fits_obj, attr) == int(
                        fits_obj.header[CryonirspMetadataKey[attr]]
                    )
                case _:
                    assert getattr(fits_obj, attr) == fits_obj.header[CryonirspMetadataKey[attr]]
        all_cryo_fits_access_attrs |= cryo_fits_access_attrs
    assert cryo_metadata_key_names == all_cryo_fits_access_attrs
