{
  description = "Fluid Attacks Blends";

  inputs = {
    flake-parts.url =
      "github:hercules-ci/flake-parts/f4330d22f1c5d2ba72d3d22df5597d123fdb60a9?shallow=1";
    nixpkgs.url =
      "github:nixos/nixpkgs/ad58b79e5abff33ce3b26c56449eff0b7bff8daf?shallow=1";
    pipeline = {
      inputs.flake-parts.follows = "flake-parts";
      url =
        "git+ssh://git@gitlab.com/fluidattacks/universe?shallow=1&rev=3f4344c3b41b1a6e4a9880bbc2e7f29969cda096&dir=common/utils/pipeline";
    };
    python-env = {
      inputs.flake-parts.follows = "flake-parts";
      url =
        "git+ssh://git@gitlab.com/fluidattacks/universe?shallow=1&rev=3f4344c3b41b1a6e4a9880bbc2e7f29969cda096&dir=common/utils/python-env";
    };
    shell-helpers = {
      inputs = {
        flake-parts.follows = "flake-parts";
        nixpkgs.follows = "nixpkgs";
      };
      url =
        "git+ssh://git@gitlab.com/fluidattacks/universe?shallow=1&rev=3f4344c3b41b1a6e4a9880bbc2e7f29969cda096&dir=common/utils/shell-helpers";
    };
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      debug = false;
      systems = [ "aarch64-darwin" "aarch64-linux" "x86_64-linux" ];

      perSystem = { inputs', pkgs, self', system, ... }:
        let
          projectPath = path: ./. + path;
          lib' = {
            envs = import ./nix/envs { inherit inputs pkgs projectPath; };
            pipeline = inputs.pipeline.lib { inherit pkgs; };
            inherit projectPath;
          };
        in {
          apps.default = {
            type = "app";
            program = "${self'.packages.blends-lint}/bin/blends-lint";
          };
          devShells = import ./nix/shells.nix { inherit lib' pkgs self'; };
          packages = import ./nix/pkgs { inherit inputs' lib' pkgs self'; };
        };
    };
}
