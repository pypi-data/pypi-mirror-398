{ inputs', lib', pkgs }:
pkgs.writeShellApplication {
  name = "blends-deploy";
  runtimeInputs = pkgs.lib.flatten [
    lib'.envs.blends.dependencies.default
    inputs'.shell-helpers.packages.helper-aws
    inputs'.shell-helpers.packages.helper-sops
    pkgs.git
    pkgs.uv
  ];
  text = ''
    if ! git diff HEAD~1 HEAD -- pyproject.toml | grep -q '^[-+]version'; then
      echo "[INFO] pyproject.toml version has not changed. Skipping deployment."
      exit 0
    fi

    # shellcheck disable=SC1091
    source helper-aws aws_login "dev" "3600"

    # Load secrets
    secrets=(
       PYPI_API_TOKEN_FLUID_BLENDS
      )
    # shellcheck disable=SC1091
    source helper-sops sops_export_vars "secrets/dev.yaml" "''${secrets[@]}"

    echo "Publishing new version for Blends"
    rm -rf "dist"
    uv build
    uv publish --token "''${PYPI_API_TOKEN_FLUID_BLENDS}"
  '';
}
