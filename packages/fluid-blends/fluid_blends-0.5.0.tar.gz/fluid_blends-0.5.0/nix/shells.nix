{ lib', pkgs, self' }: {
  default = pkgs.mkShell {
    packages = pkgs.lib.flatten [
      lib'.envs.blends.dependencies.editable
      lib'.envs.blends.envars
      (pkgs.lib.attrValues self'.packages)
    ];
    env = {
      PRODUCT_ID = "blends";
      UV_NO_SYNC = "1";
      UV_PYTHON = "${lib'.envs.blends.venv.editable}/bin/python";
      UV_PYTHON_DOWNLOADS = "never";
    };
    shellHook = ''
      unset PYTHONPATH
      export BLENDS_PYTHON_INTERPRETER="${lib'.envs.blends.venv.editable}/bin/python"
      source blends-envars
    '';
  };
}
