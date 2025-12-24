from pathlib import Path
from textwrap import dedent


def client_pyproject(app_name: str):
    return dedent(f"""\
[build-system]
requires = ["hatchling>=1.25", "versioningit>=3.3"]
build-backend = "hatchling.build"

[project]
name = "{app_name}-client"
dynamic = ["version"]
description = "Typed RPC client + generated GraphQL assets for {app_name}"
requires-python = ">=3.10"
dependencies = [
  "httpx>=0.24",
  "pydantic>=2.0",
]

[tool.hatch.version]
source = "versioningit"

[tool.hatch.build.targets.wheel]
packages = ["src/{app_name}_client"]

[tool.hatch.build.targets.wheel.force-include]
"../graphql/fragments" = "{app_name}_client/graphql/fragments"
"../graphql/mutations" = "{app_name}_client/graphql/mutations"
"../graphql/queries"   = "{app_name}_client/graphql/queries"
"../graphql/schema"    = "{app_name}_client/graphql/schema"

[tool.hatch.build.targets.sdist]
include = [
  "src/**",
]

[tool.hatch.build.targets.sdist.force-include]
"../graphql/fragments" = "{app_name}_client/graphql/fragments"
"../graphql/mutations" = "{app_name}_client/graphql/mutations"
"../graphql/queries"   = "{app_name}_client/graphql/queries"
"../graphql/schema"    = "{app_name}_client/graphql/schema"

[tool.versioningit]
default-version = "0+unknown"

[tool.versioningit.format]
distance = "0+g{{rev}}"
dirty = "0+g{{rev}}.d{{build_date:%Y%m%d}}"
distance-dirty = "0+g{{rev}}.d{{build_date:%Y%m%d}}"

[tool.versioningit.vcs]
method = "git"
default-tag = "0"
""").lstrip()


def write_client_pyproject_toml(out_dir: Path, app_name: str) -> None:
    (out_dir / "pyproject.toml").write_text(
        client_pyproject(app_name),
        encoding="utf-8",
    )
