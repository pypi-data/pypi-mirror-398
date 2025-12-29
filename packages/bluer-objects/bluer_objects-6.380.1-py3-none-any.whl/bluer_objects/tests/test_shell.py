import pytest

from bluer_objects.host.functions import shell


@pytest.mark.parametrize(
    ["command"],
    [
        ["ls"],
        ["ls *"],
        [
            [
                "ls",
                "*",
            ],
        ],
    ],
)
def test_shell(command: str):
    success = shell(
        command=command,
        log=True,
    )
    assert success

    success, output = shell(
        command=command,
        return_output=True,
        log=True,
    )
    assert success
    assert isinstance(output, list)
    for item in output:
        assert isinstance(item, str)
