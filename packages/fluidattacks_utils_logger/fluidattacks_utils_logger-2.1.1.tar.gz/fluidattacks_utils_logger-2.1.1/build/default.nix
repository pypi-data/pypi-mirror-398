{ nixpkgs, builders, scripts, src, }: {
  inherit src;
  root_path = "observes/common/utils-logger";
  module_name = "fluidattacks_utils_logger";
  pypi_token_var = "UTILS_LOGGER_TOKEN";
  override = b: b;
}
