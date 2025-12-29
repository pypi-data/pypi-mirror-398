from typing import List, Dict


# {image,jpg : url}
def ImageItems(items: Dict[str, str]) -> List[str]:
    def add_raw(url: str) -> str:
        return (
            f"{url}?raw=true" if "github.com" in url and "raw=true" not in url else url
        )

    return [
        (
            ""
            if not image
            else "[![image]({})]({})".format(
                add_raw(image), url if url else add_raw(image)
            )
        )
        for image, url in items.items()
    ]


# name, url, marquee, description
def Items(
    items: List[Dict[str, str]],
    sort: bool = False,
) -> List[str]:
    output = [
        (
            "{}[![image]({})]({}) {}".format(
                (
                    "[`{}`]({}) ".format(
                        item["name"],
                        item.get(
                            "url",
                            "#",
                        ),
                    )
                    if item["name"]
                    else ""
                ),
                item.get(
                    "marquee",
                    "https://github.com/kamangir/assets/raw/main/blue-plugin/marquee.png?raw=true",
                ),
                item.get(
                    "url",
                    "#",
                ),
                item.get("description", ""),
            )
            if "name" in item
            else ""
        )
        for item in items
    ]

    if sort:
        output = sorted(output)

    return output


# dict of {name, url, marquee, description}
def Items_of_dict(
    dict_of_things: Dict[str, Dict],
) -> List[str]:
    return Items(
        sorted(
            [
                {
                    "order": info.get("order", thing_name),
                    "name": thing_name,
                    "marquee": info.get("marquee", ""),
                    "url": f"./{thing_name}.md",
                }
                for thing_name, info in dict_of_things.items()
                if thing_name != "template"
            ],
            key=lambda x: x["order"],
        )
    )


# dict of {name, url, marquee, description}
def list_of_dict(
    dict_of_things: Dict[str, Dict],
) -> List[str]:
    return [
        item["text"]
        for item in sorted(
            [
                {
                    "text": f"- [{thing_name}](./{thing_name}.md)",
                    "order": info.get("order", thing_name),
                }
                for thing_name, info in dict_of_things.items()
                if thing_name != "template"
            ],
            key=lambda x: x["order"],
        )
    ]
