import sys

import fledge_cli


def test_import() -> None:
    dir(fledge_cli)  # Ensure package can be used
    assert "fledge_cli" in sys.modules
