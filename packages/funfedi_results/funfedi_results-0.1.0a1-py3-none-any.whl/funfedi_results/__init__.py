from .transform import transform_feature_result
from .archive.parse import features_from_result, load_archive
from .archive.types import FeatureResult, ResultDescription
from .latest import latest_for_app_name

__all__ = ["feature_status", "FeatureResult"]


def feature_status(app_name: str):
    case_version, app_version = latest_for_app_name(app_name)
    if not case_version or not app_version:
        raise Exception("Failed to find test data")

    desc = ResultDescription(case_version, app_name, app_version)

    result = load_archive(desc)
    features = features_from_result(result)

    feature_status_map = {}
    for feature in features:
        feature_status_map.update(transform_feature_result(feature))

    return feature_status_map
