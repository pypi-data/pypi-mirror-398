{ lib', pkgs }:
let
  rules = {
    default = lib'.pipeline.core.rules.titleRule {
      products = [ "all" "blends" ];
      types = [ ];
    };
    noChore = lib'.pipeline.core.rules.titleRule {
      products = [ "all" "blends" ];
      types = [ "feat" "fix" "refac" ];
    };
  };
  tests = let
    testCategories = [ "all" "content_unittesting" ];
    ciCategories = pkgs.lib.remove "all" testCategories;
    jobNames = builtins.map (category: "blends-test ${category}") ciCategories;
    categoryName = jobName:
      pkgs.lib.strings.removePrefix "blends-test " jobName;
  in pkgs.lib.attrsets.genAttrs jobNames (jobName:
    lib'.pipeline.jobs.nix {
      component = "blends";
      rules = lib'.pipeline.rules.dev ++ [ rules.noChore ];
      script = [ "nix run .#blends-test ${categoryName jobName}" ];
      stage = lib'.pipeline.stages.test;
      tags = [ lib'.pipeline.tags.aarch64 ];
      artifacts = {
        paths = [ "blends/.coverage.*" ];
        expire_in = "1 day";
      };
    });
in lib'.pipeline.sync {
  name = "blends-pipeline";
  targetPath = ".gitlab-ci.yaml";
  pipeline = {
    blends-lint = lib'.pipeline.jobs.nix {
      cache = {
        key = "$CI_COMMIT_REF_NAME-blends-lint";
        paths = [ "blends/.ruff_cache" "blends/.mypy_cache" ];
      };
      component = "blends";
      rules = lib'.pipeline.rules.dev ++ [ rules.noChore ];
      script = [ "nix run .#blends-lint" ];
      stage = lib'.pipeline.stages.test;
      tags = [ lib'.pipeline.tags.aarch64 ];
    };
    blends-pipeline = lib'.pipeline.jobs.nix {
      component = "blends";
      rules = lib'.pipeline.rules.dev ++ [ rules.noChore ];
      script = [ "nix run .#blends-pipeline" ];
      stage = lib'.pipeline.stages.test;
      tags = [ lib'.pipeline.tags.aarch64 ];
    };
    blends-coverage = lib'.pipeline.jobs.nix {
      component = ".";
      needs = builtins.attrNames tests;
      rules = lib'.pipeline.rules.dev ++ [ rules.noChore ];
      script = [ "nix run ./blends#blends-coverage" ];
      stage = lib'.pipeline.stages.deploy;
      tags = [ lib'.pipeline.tags.aarch64 ];
      variables.GIT_DEPTH = 3;
    };
    blends-deploy = lib'.pipeline.jobs.nix {
      component = "blends";
      rules = lib'.pipeline.rules.prod ++ [ rules.noChore ];
      script = [ "nix run .#blends-deploy" ];
      stage = lib'.pipeline.stages.deploy;
      tags = [ lib'.pipeline.tags.aarch64 ];
    };
  } // tests;
}
