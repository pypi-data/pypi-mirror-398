from . import feature_status


def test_feature_status():
    result = feature_status("mitra")

    assert result == {
        "post": "passed",
        "public_timeline": "passed",
        "webfinger": "passed",
    }
