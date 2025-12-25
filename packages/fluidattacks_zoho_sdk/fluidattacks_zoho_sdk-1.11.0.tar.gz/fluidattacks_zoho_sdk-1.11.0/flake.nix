{
  description = "Zoho API auth SDK";

  inputs = {
    observes_flake_builder = {
      url =
        "git+ssh://git@gitlab.com/fluidattacks/universe?shallow=1&rev=c5053864bb838edbe226d74a650d901c0270843b&dir=observes/common/std_flake_2";
    };
  };

  outputs = { self, ... }@inputs:
    let
      build_args = { system, python_version, nixpkgs, builders, scripts }:
        import ./build {
          inherit nixpkgs builders scripts;
          src = import ./build/filter.nix nixpkgs.nix-filter self;
        };
    in { packages = inputs.observes_flake_builder.outputs.build build_args; };
}
