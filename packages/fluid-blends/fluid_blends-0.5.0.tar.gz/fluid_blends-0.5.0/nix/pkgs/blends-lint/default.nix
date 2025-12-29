{ lib', pkgs }:
pkgs.writeShellApplication {
  name = "blends-lint";
  runtimeInputs = lib'.envs.blends.dependencies.editable;
  text = ''
    ruff format --config ruff.toml --exit-non-zero-on-format
    ruff check --config ruff.toml --fix --exit-non-zero-on-fix

    mypy --config-file mypy.ini blends
    mypy --config-file mypy.ini test

    deptry . --known-first-party blends
  '';
}
