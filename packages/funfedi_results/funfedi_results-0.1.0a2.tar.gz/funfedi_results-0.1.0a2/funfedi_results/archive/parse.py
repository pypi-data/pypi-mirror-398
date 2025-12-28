import json
import logging
import zipfile
from .types import FeatureResult, LoadedResult, ResultDescription

logger = logging.getLogger(__name__)


def name_to_type(name: str) -> str:
    """
    ```
    >>> name_to_type("verify/allure-results/fa6bc2a7-5743-432b-9ad6-0ddcf14619e0-container.json")
    'container'

    ```
    """

    return name.split(".")[0].split("-")[-1]


def load_archive(desc: ResultDescription) -> LoadedResult:
    result = LoadedResult([], [], {})
    with zipfile.ZipFile(desc.filename) as f:
        for name in f.namelist():
            parsed = json.loads(f.read(name))
            match name_to_type(name):
                case "container":
                    result.containers.append(parsed)
                case "result":
                    result.results.append(parsed)
                case "attachment":
                    attachment_name = name.removesuffix("-attachment.json").split("/")[
                        -1
                    ]
                    result.attachments[attachment_name] = parsed
                case _:
                    logger.warning("Unknown name %s", name)
            ...
    return result


def features_from_result(result: LoadedResult):
    features: dict[str, FeatureResult] = {}
    for x in result.results:
        title_path = x.get("titlePath")
        if not title_path:
            continue
        if title_path[0] == "features":
            parsed = FeatureResult.from_data(x)
            if parsed and parsed.name in features:
                if features[parsed.name].start < parsed.start:
                    features[parsed.name] = parsed
            else:
                features[parsed.name] = parsed

    return list(features.values())
