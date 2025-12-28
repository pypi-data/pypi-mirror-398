from .parse import features_from_result, load_archive
from .types import ResultDescription


def test_load():
    desc = ResultDescription("0.1.2", "mitra", "v4.15.0")

    result = load_archive(desc)

    assert result


def test_features():
    desc = ResultDescription("0.1.2", "mitra", "v4.15.0")
    result = load_archive(desc)
    assert len(features_from_result(result)) > 0
