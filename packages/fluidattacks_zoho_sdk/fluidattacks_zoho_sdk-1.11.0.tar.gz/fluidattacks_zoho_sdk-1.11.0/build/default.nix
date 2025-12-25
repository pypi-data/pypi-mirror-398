{ nixpkgs, builders, scripts, src, }: {
  inherit src;
  root_path = "observes/sdk/zoho";
  module_name = "fluidattacks_zoho_sdk";
  pypi_token_var = "ZOHO_SDK_TOKEN";
  override = b: b;
}
