import pytest

from bluer_objects.env import abcli_path_git
from bluer_objects.README.consts import (
    assets_path,
    assets_url,
    designs_repo,
    designs_url,
    github_kamangir,
)


@pytest.mark.parametrize(
    ["suffix"],
    [
        ["this"],
        ["that/which"],
    ],
)
@pytest.mark.parametrize(
    ["volume"],
    [
        [""],
        ["2"],
        [2],
    ],
)
def test_README_assets(
    suffix: str,
    volume: str,
):
    volume_url = assets_url(volume=volume)
    assert isinstance(volume_url, str)
    assert volume_url.startswith(github_kamangir)

    # ---

    suffix_url = assets_url(
        suffix=suffix,
        volume=volume,
    )

    assert isinstance(suffix_url, str)
    assert suffix_url.endswith(suffix)
    assert volume_url in suffix_url

    # ---

    suffix_path = assets_path(
        suffix=suffix,
        volume=volume,
    )

    assert isinstance(suffix_url, str)
    assert suffix_path.endswith(suffix)
    assert abcli_path_git in suffix_path


@pytest.mark.parametrize(
    ["suffix"],
    [
        ["this"],
        ["that/which"],
    ],
)
def test_README_designs_url(suffix):
    url = designs_url(suffix=suffix)

    assert isinstance(url, str)
    assert url.startswith(designs_repo)
    assert url.endswith(suffix)
