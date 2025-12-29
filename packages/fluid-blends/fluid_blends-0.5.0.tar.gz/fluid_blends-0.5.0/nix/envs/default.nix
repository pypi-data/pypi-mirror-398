{ inputs, pkgs, projectPath }: {
  blends = import ./blends/default.nix { inherit inputs pkgs projectPath; };
}
