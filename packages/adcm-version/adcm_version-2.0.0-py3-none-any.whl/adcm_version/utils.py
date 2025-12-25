import re
from enum import Enum

from version_utils import rpm

PATTERN_OLD_ADCM_VERSION = re.compile(r"^(\d{4}\.\d{1,2}\.\d{1,2}\.\d{1,2})([-_][0-9a-z]{8})?$")


class ComparisonResult(int, Enum):
    NEWER = 1
    OLDER = -1
    EQUAL = 0


def is_legacy(adcm_version: str) -> bool:
    """
    Check ADCM version

    :param adcm_version: An ADCM version
    :return: True (if ``version`` is old), False (else)
    """

    if PATTERN_OLD_ADCM_VERSION.match(string=adcm_version) is None:
        return False

    return True


def compare_adcm_versions(this: str, other: str) -> ComparisonResult:
    """
    Compare two ADCM version strings.

    Comparison result is a statement about `this`.
    """

    this_ver_is_legacy = is_legacy(adcm_version=this)
    other_ver_is_legacy = is_legacy(adcm_version=other)

    if this_ver_is_legacy != other_ver_is_legacy:
        if this_ver_is_legacy:
            return ComparisonResult.OLDER

        return ComparisonResult.NEWER

    return _compare(this=this, other=other)


def compare_prototype_versions(this: str, other: str) -> ComparisonResult:
    """
    Compare two prototype version strings for ADCM objects.

    Comparison result is a statement about `this`.
    """

    return _compare(this=this, other=other)


def _compare(this: str, other: str) -> ComparisonResult:
    return ComparisonResult(rpm.compare_versions(version_a=this, version_b=other))
