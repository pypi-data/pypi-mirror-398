from bluer_objects.README.items import ImageItems, Items, Items_of_dict, list_of_dict
from bluer_objects.README.consts import assets, assets2
from bluer_objects import markdown
from bluer_objects import env

dict_of_validations = dict_of_validations = {
    "village-1": {
        "ugv_name": [
            "arzhang1:ugv",
            "arzhang2:ugv",
            "arzhang3:anchor",
        ],
        "items": ImageItems(
            {
                f"{assets2}/arzhang/20250905_120526.jpg": "",
                f"{assets2}/arzhang/20250905_120808.jpg": "",
                f"{assets2}/arzhang/20250905_121030.jpg": "",
                f"{assets2}/arzhang/20250905_121032.jpg": "",
                f"{assets2}/arzhang/20250905_121702.jpg": "",
                f"{assets2}/arzhang/20250905_121711.jpg": "",
            }
        ),
        "marquee": f"{assets}/2025-09-05-11-48-27-d56azo/VID-20250905-WA0014_1.gif",
    },
    "village-2": {
        "ugv_name": [
            "arzhang1:ugv",
            "arzhang2:ugv",
            "arzhang3:anchor",
        ],
        "items": ImageItems(
            {
                f"{assets2}/arzhang/20250922_094548.jpg": "",
                f"{assets2}/arzhang/20250922_101156.jpg": "",
                f"{assets2}/arzhang/20250922_101409.jpg": "",
                f"{assets2}/arzhang/20250922_101557.jpg": "",
                f"{assets2}/arzhang/20250922_101653.jpg": "",
                f"{assets2}/arzhang/20250922_102822.jpg": "",
            }
        ),
        "macros": {
            "debug_objects": markdown.generate_table(
                Items(
                    [
                        {
                            "name": object_name,
                            "url": "https://{}.{}/{}".format(
                                env.S3_PUBLIC_STORAGE_BUCKET,
                                env.S3_STORAGE_ENDPOINT_URL.split("https://", 1)[1],
                                f"{object_name}.tar.gz",
                            ),
                            "marquee": f"{assets}/{object_name}/{object_name}.gif",
                        }
                        for object_name in [
                            "swallow-debug-2025-09-22-09-47-32-85hag3",
                            "swallow-debug-2025-09-22-09-59-29-emj29v",
                            "swallow-debug-2025-09-22-10-01-01-uzray6",
                            "swallow-debug-2025-09-22-10-06-19-hcyl1v",
                            "swallow-debug-2025-09-22-10-09-44-z6q9kn",
                            "swallow-debug-2025-09-22-10-19-35-mobajm",
                        ]
                    ]
                ),
                cols=3,
                log=False,
            ),
        },
        "marquee": f"{assets}/arzhang/20250922_101202_1.gif",
    },
}


def test_ImageItems():
    items = ImageItems(
        {
            f"{assets2}/swallow/20250701_2206342_1.gif": "",
            f"{assets2}/swallow/20250913_203635~2_1.gif": "",
        }
    )

    assert isinstance(items, list)
    for item in items:
        assert isinstance(item, str)


def test_Items():
    items = Items(
        [
            {
                "name": "yolo",
                "description": "a yolo interface.",
                "marquee": "https://github.com/kamangir/assets/raw/main/swallow-debug-2025-09-16-19-53-19-4yzsp8/swallow-debug-2025-09-16-19-53-19-4yzsp8-2.gif?raw=true",
                "url": "./bluer_algo/docs/yolo",
            },
            {
                "name": "tracker",
                "marquee": "https://github.com/kamangir/assets/raw/main/tracker-camshift-2025-07-16-11-07-52-4u3nu4/tracker.gif?raw=true",
                "description": "a visual tracker.",
                "url": "./bluer_algo/docs/tracker",
            },
            {
                "name": "image classifier",
                "marquee": "https://github.com/kamangir/assets/raw/main/swallow-model-2025-07-11-15-04-03-2glcch/evaluation.png?raw=true",
                "description": "an image classifier.",
                "url": "./bluer_algo/docs/image_classifier",
            },
        ]
    )

    assert isinstance(items, list)
    for item in items:
        assert isinstance(item, str)


def test_Items_of_dict():
    items = Items_of_dict(dict_of_validations)

    assert isinstance(items, list)
    for item in items:
        assert isinstance(item, str)


def test_list_of_dict():
    items = list_of_dict(dict_of_validations)

    assert isinstance(items, list)
    for item in items:
        assert isinstance(item, str)
