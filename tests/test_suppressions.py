import pytest

from agentic_owasp.scanner import is_suppressed

RULE = "mcp-shell-injection"


@pytest.mark.parametrize(
    ("source", "line"),
    [
        (["os.system(cmd)  # nosemgrep"], 1),
        (["os.system(cmd)  # nosem"], 1),
        (["os.system(cmd)  # nosemgrep: mcp-shell-injection"], 1),
        (["os.system(cmd)  # nosemgrep: mcp-code-eval, mcp-shell-injection"], 1),
        (["os.system(cmd)  # nosemgrep: rules.python.mcp-shell-injection"], 1),
        (["exec(cmd); // nosemgrep"], 1),
        (["exec(cmd); /* nosemgrep */  "], 1),
        (["os.system(cmd)  # nosemgrep   "], 1),
        (["# nosemgrep", "os.system(cmd)"], 2),
        (["    // nosemgrep: mcp-shell-injection", "    exec(cmd);"], 2),
    ],
    ids=lambda value: value if isinstance(value, int) else value[-1],
)
def test_nosemgrep_comment_suppresses(source: list[str], line: int) -> None:
    assert is_suppressed(source, line, RULE)


@pytest.mark.parametrize(
    ("source", "line"),
    [
        (["os.system(cmd)"], 1),
        (["os.system(cmd)  # nosemgrep: mcp-code-eval"], 1),
        (["os.system(cmd)  # not a nosemgrep marker"], 1),
        (["os.system(cmd)  # nosemgrep because reasons"], 1),
        (["os.system(cmd)  # nosemgrep: $$$"], 1),
        (["os.system(cmd)  # nosemgrep:"], 1),
        (["os.system(cmd)  # nosemgrep_disabled"], 1),
        (['print("nosemgrep")'], 1),
        (["x = 1  # nosemgrep", "os.system(cmd)"], 2),
        (["# nosemgrep", "", "os.system(cmd)"], 3),
        ([], 1),
    ],
    ids=lambda value: value if isinstance(value, int) else (value[-1] if value else "empty"),
)
def test_other_comments_do_not_suppress(source: list[str], line: int) -> None:
    assert not is_suppressed(source, line, RULE)
