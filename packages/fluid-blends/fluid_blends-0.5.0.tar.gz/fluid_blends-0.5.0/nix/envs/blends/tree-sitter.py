import os  # noqa: INP001
import tree_sitter

from pathlib import Path


GRAMMARS: dict[str, str] = {
    # Grammars required because not available on pypi as of 12/25
    "dart": os.environ["GRAMMAR_DART"],
}


def main() -> None:
    # Ignored, nix standard behavior sets "out" not "OUT"
    out: str = os.environ["out"]  # noqa: SIM112

    Path(out).mkdir(parents=True, exist_ok=True)

    for grammar, src in GRAMMARS.items():
        path = Path(out) / f"{grammar}.so"
        tree_sitter.Language.build_library(str(path), [src])


if __name__ == "__main__":
    main()
