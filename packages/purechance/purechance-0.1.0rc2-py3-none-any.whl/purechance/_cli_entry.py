import sys


def main() -> None:
    try:
        from purechance import cli
    except (ImportError, ModuleNotFoundError) as exc:
        print(
            "CLI dependencies missing. Use: pip install 'purechance[cli]'",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    cli.main()
