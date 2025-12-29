{ pkgs }:
let
  grammarDart = builtins.fetchTarball {
    url =
      "https://github.com/UserNobody14/tree-sitter-dart/archive/e81af6ab94a728ed99c30083be72d88e6d56cf9e.tar.gz";
    sha256 = "sha256:0zl46vkm4p1jmivmnpyyzc58fwhx5frfgi0rfxna43h0qxdv62wy";
  };
  patchedBin = pkgs.python311Packages.tree-sitter.overridePythonAttrs
    (oldAttrs: {
      src = pkgs.fetchFromGitHub {
        owner = "tree-sitter";
        repo = "py-tree-sitter";
        rev = "refs/tags/v0.21.1";
        sha256 = "sha256-U4ZdU0lxjZO/y0q20bG5CLKipnfpaxzV3AFR6fGS7m4=";
        fetchSubmodules = true;
      };

      dependencies = [ pkgs.python311Packages.setuptools ];
    });
in pkgs.stdenv.mkDerivation {
  buildPhase = ''
    export GRAMMAR_DART="${grammarDart}"

    python tree-sitter.py
  '';
  name = "blends-tree-sitter-patch";
  nativeBuildInputs = [ patchedBin ];
  src = ./.;
}
