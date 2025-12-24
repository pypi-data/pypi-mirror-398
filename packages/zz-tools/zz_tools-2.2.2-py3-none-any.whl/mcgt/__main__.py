import argparse


# Version découverte de manière robuste
def get_version():
    try:
        from . import __version__ as v

        return v
    except Exception:
        return "0"


def main(argv=None):
    p = argparse.ArgumentParser(prog="mcgt", description="mcgt command-line")
    p.add_argument("--version", action="store_true", help="print version and exit")
    args, _ = p.parse_known_args(argv)
    if args.version:
        print(get_version())
        return 0
    # Si aucun argument, juste afficher l'aide et sortir 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
