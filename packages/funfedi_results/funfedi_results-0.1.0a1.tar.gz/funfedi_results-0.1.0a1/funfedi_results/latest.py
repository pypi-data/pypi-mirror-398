from glob import glob
import re
import semver

pattern = re.compile(r"test_results/(.*)?/(.*)?__(.*).zip")


def to_semver(version, skip_prerelease=True):
    try:
        if version.count(".") == 1:
            version = "0." + version
        if "a" in version:
            version = version.split("a")[0]
        result = semver.Version.parse(version.removeprefix("v"))

        if result.prerelease and skip_prerelease:
            return semver.Version(0)
        return result
    except Exception:
        return semver.Version(0)


def later_version(a, b):
    """
    ```
    >>> later_version("v4.5.2", "v4.6.2")
    'v4.6.2'

    ```
    """
    if to_semver(a) > to_semver(b):
        return a
    return b


def latest_for_app_name(name: str):
    case_version = None
    app_version = None
    for x in glob(f"test_results/*/{name}__*"):
        m = re.match(pattern, x)
        if not m:
            raise Exception("Does not match regex")
        case_version = later_version(case_version, m.group(1))
        app_version = later_version(app_version, m.group(3))

    return case_version, app_version
