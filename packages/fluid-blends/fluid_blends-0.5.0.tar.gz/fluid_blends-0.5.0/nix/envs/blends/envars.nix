{ pkgs, projectPath }:
let
  treeSitter = pkgs.callPackage ./tree-sitter.nix { };
  treeSitterStaticNodeFields = projectPath "/static/node_types";
in pkgs.writeShellApplication {
  bashOptions = [ ];
  name = "blends-envars";
  text = ''
    export BLENDS_TREE_SITTER_PARSERS_DIR="${treeSitter}"
    export BLENDS_TREE_SITTER_STATIC_NODE_FIELDS="${treeSitterStaticNodeFields}"

    export PRODUCT_ID="blends"
  '';
}
