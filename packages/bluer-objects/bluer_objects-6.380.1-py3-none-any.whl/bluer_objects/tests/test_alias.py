import pytest
from bluer_objects import NAME
from bluer_objects.README.alias import list_of_aliases


@pytest.mark.parametrize(
    ["alias_name", "expected_to_exist", "as_markdown", "itemized"],
    [
        ["void", False, False, False],
        ["host", True, True, False],
        ["host", True, True, True],
    ],
)
def test_alias_list_of_aliases(
    alias_name: str,
    expected_to_exist: bool,
    as_markdown: bool,
    itemized: bool,
):
    output = list_of_aliases(
        module_name=NAME,
        as_markdown=as_markdown,
        itemized=itemized,
    )

    assert isinstance(output, list)
    for thing in output:
        assert isinstance(thing, str)

    if as_markdown:
        return

    assert (alias_name in output) == expected_to_exist
