path_filter: src:
path_filter {
  root = src;
  include = [
    "fluidattacks_zoho_sdk"
    "tests"
    "pyproject.toml"
    "mypy.ini"
    "ruff.toml"
    "uv.lock"
  ];
}
