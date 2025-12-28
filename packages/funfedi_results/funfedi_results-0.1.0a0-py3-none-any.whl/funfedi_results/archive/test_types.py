from .types import FeatureResult


feature_info = {
    "name": "Can fetch public timeline",
    "status": "passed",
    "steps": [
        {
            "name": "Given A Fediverse application",
            "status": "passed",
            "start": 1766562342506,
            "stop": 1766562342507,
        },
        {
            "name": "Given the object parsing is build",
            "status": "passed",
            "start": 1766562342507,
            "stop": 1766562342587,
        },
        {
            "name": 'When a message is send from "pasture-one-actor" to the application',
            "status": "passed",
            "start": 1766562342587,
            "stop": 1766562342829,
        },
        {
            "name": "Then the public timeline contains the message",
            "status": "passed",
            "start": 1766562342829,
            "stop": 1766562343902,
        },
    ],
    "start": 1766562342505,
    "stop": 1766562343904,
    "uuid": "c8244d31-cfd8-489a-a76a-69737296e178",
    "historyId": "8aa6b52f61f474116aa15483f5f3bdf6",
    "testCaseId": "6acc62704f6f098cc2540004d0494fcc",
    "fullName": "mitra: Funfedi Connect support: Can fetch public timeline",
    "labels": [
        {"name": "severity", "value": "normal"},
        {"name": "tag", "value": "public-timeline"},
        {"name": "feature", "value": "mitra: Funfedi Connect support"},
        {"name": "framework", "value": "behave"},
        {"name": "language", "value": "cpython3"},
    ],
    "titlePath": ["features", "mitra: Funfedi Connect support"],
}


def test_feature_result():
    result = FeatureResult.from_data(feature_info)

    assert result.name == "mitra: Funfedi Connect support: Can fetch public timeline"
    assert result.status == "passed"
    assert result.tags == ["public-timeline"]
