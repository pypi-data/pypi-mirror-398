from funfedi_connect import ImplementedFeature
from funfedi_results.archive.types import FeatureResult


def tags_to_features(tags: list[str]):
    """
    ```
    >>> tags_to_features(["webfinger", "other"])
    ['webfinger']

    ```
    """
    result = []
    for tag in tags:
        try:
            result.append(str(ImplementedFeature.from_tag(tag)))
        except Exception:
            ...
    return result


def transform_feature_result(result: FeatureResult):
    return {feature: result.status for feature in tags_to_features(result.tags)}
