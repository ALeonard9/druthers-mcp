# pylint: disable=missing-module-docstring, missing-function-docstring
# Branding regression tests (mcp#44): the server must present as Druthers, and
# the dead personal-brand name must stay gone from the shipped code.
import pathlib

import druthers_mcp
from druthers_mcp import server


def test_server_registers_as_druthers():
    assert server.mcp.name == "druthers"


def test_logger_uses_druthers_namespace():
    assert server.logger.name == "druthers_mcp"


def test_python_sources_have_no_aleonard_branding():
    pkg_dir = pathlib.Path(druthers_mcp.__file__).parent
    tests_dir = pathlib.Path(__file__).parent
    offenders = []
    for root in (pkg_dir, tests_dir):
        for path in root.rglob("*.py"):
            if path.resolve() == pathlib.Path(__file__).resolve():
                continue
            if "aleonard" in path.read_text().lower():
                offenders.append(str(path))
    assert not offenders
