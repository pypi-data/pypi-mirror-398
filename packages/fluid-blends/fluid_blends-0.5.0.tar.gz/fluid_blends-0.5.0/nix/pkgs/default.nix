{ inputs', lib', pkgs, self' }: {
  default = self'.packages.blends-lint;

  blends-deploy =
    import ./blends-deploy/default.nix { inherit inputs' lib' pkgs; };

  blends-lint = import ./blends-lint/default.nix { inherit lib' pkgs; };
  blends-pipeline = import ./blends-pipeline/default.nix { inherit lib' pkgs; };
  blends-test = import ./blends-test/default.nix { inherit lib' pkgs; };
  blends-coverage = import ./blends-coverage/default.nix { inherit pkgs; };
}
