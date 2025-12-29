{ inputs, pkgs, projectPath }:
let
  envars = pkgs.callPackage ./envars.nix { inherit projectPath; };
  venv = import ./venv.nix { inherit inputs pkgs projectPath; };

  dependencies = let osDependencies = [ pkgs.git ];
  in {
    default = pkgs.lib.flatten [ venv.default osDependencies ];
    editable = pkgs.lib.flatten [ venv.editable osDependencies ];
  };
in { inherit dependencies envars venv; }
