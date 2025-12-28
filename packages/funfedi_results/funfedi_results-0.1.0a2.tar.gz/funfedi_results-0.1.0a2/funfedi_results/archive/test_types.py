from .types import FeatureResult


feature_info = {
    "name": "Can fetch public timeline",
    "status": "passed",
    "steps": [
        {
            "name": "Given A Fediverse application",
            "status": "passed",
            "start": 1766579158709,
            "stop": 1766579158709,
        },
        {
            "name": "When a message is posted from the application",
            "status": "passed",
            "start": 1766579158710,
            "stop": 1766579158814,
        },
        {
            "name": 'Then "pasture-one-actor" can read it',
            "status": "passed",
            "attachments": [
                {
                    "name": "Created object",
                    "source": "ebbc2ec6-179a-4061-87e6-495e8c06411f-attachment.json",
                    "type": "application/json",
                }
            ],
            "start": 1766579158814,
            "stop": 1766579158863,
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
    assert result.attachments == {
        "Created object": "ebbc2ec6-179a-4061-87e6-495e8c06411f"
    }
