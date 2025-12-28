from funfedi_results.archive.types import FeatureResult
from . import transform_feature_result


def test_transform_result():
    result = FeatureResult(
        name="app",
        status="passed",
        tags=["webfinger", "other"],
        start=12,
        attachments={},
    )

    transformed = transform_feature_result(result)

    assert transformed == {"webfinger": "passed"}
