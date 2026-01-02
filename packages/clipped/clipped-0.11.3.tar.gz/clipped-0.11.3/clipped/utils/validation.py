from typing import List, Optional, Union

from clipped.utils.lists import to_list


def validate_tags(
    tags: Optional[Union[str, List[str]]], validate_yaml: bool = False
) -> Optional[List[str]]:
    if not tags:
        return None

    if validate_yaml and isinstance(tags, str) and ("[" in tags and "]" in tags):
        import yaml

        tags = yaml.safe_load(tags)

    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",")]
    tags = to_list(tags, to_unique=True)
    tags = [tag.strip() for tag in tags if (tag and isinstance(tag, str))]
    return [t for t in tags if t]
