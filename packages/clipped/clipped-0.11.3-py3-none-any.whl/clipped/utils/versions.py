import re


def get_loose_version(vstring: str):
    from clipped._vendor.version import LooseVersion

    return LooseVersion(vstring)


def clean_version_for_compatibility(version: str):
    return "-".join(version.lstrip("v").replace(".", "-").split("-")[:3])


def clean_version_for_check(version: str):
    if not version:
        return version
    return ".".join(version.lstrip("v").replace("-", ".").split(".")[:3])


def clean_version_post_suffix(version: str):
    return re.sub(r"(-?)p\d+$", "", version)


def compare_versions(current: str, reference: str, comparator: str) -> bool:
    current = get_loose_version(current)
    reference = get_loose_version(reference)

    if comparator == "=":
        return current == reference

    if comparator == "!=":
        return current != reference

    if comparator == "<":
        return current < reference

    if comparator == "<=":
        return current <= reference

    if comparator == ">":
        return current > reference

    if comparator == ">=":
        return current >= reference

    raise ValueError("Comparator `{}` is not supported.".format(comparator))
