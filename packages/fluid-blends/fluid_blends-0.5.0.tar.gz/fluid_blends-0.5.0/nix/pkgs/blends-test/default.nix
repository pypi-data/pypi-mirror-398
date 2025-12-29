{ lib', pkgs }:

pkgs.writeShellApplication {
  name = "blends-test";
  runtimeInputs = pkgs.lib.flatten [
    lib'.envs.blends.dependencies.editable
    lib'.envs.blends.envars
  ];
  text = ''
    # shellcheck disable=SC1091
    source blends-envars

    category="${"$"}{1:-all}"

    pytest_flags=(
      --cov=blends
      --cov-config=.coveragerc
      --cov-report=term
      --cov-report=xml:.coverage.xml
      --disable-warnings
      --no-cov-on-fail
      -vvv
    )

    if [ "$category" != "all" ]; then
      pytest_flags+=(--blends-test-group="$category")
    fi

    pytest "''${pytest_flags[@]}" test/

    if [ -f .coverage ]; then
      mv .coverage ".coverage.$category"
    fi
  '';
}
