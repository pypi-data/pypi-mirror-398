path_filter: src:
path_filter {
  root = src;
  include = [
    "fluidattacks_utils_logger"
    "tests"
    "pyproject.toml"
    "mypy.ini"
    "ruff.toml"
    "uv.lock"
  ];
}
