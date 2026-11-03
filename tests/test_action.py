import tomllib

import yaml
from catalog import REPO_ROOT

WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def test_release_smoke_consumes_the_current_version() -> None:
    version = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]["version"]
    workflow = yaml.safe_load((WORKFLOWS / "release-smoke.yml").read_text())
    remote = [
        step["uses"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if step.get("uses", "").startswith("djamshedkarimov/agentic-owasp-skills@")
    ]
    assert remote == [f"djamshedkarimov/agentic-owasp-skills@v{version}"]
