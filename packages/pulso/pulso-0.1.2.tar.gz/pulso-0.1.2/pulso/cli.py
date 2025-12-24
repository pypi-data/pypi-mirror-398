"""Pulso CLI entrypoint."""

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pulso", description="Pulso command line tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run the Pulso HTTP API server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    serve_parser.add_argument("--port", type=int, default=8080, help="Bind port")
    serve_parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    return parser


def _run_serve(args: argparse.Namespace) -> int:
    try:
        from .api import create_app
    except ModuleNotFoundError as exc:
        if exc.name == "flask":
            print("Missing dependency: install with `pip install pulso[api]`", file=sys.stderr)
            return 1
        raise

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "serve":
        raise SystemExit(_run_serve(args))

    raise SystemExit(1)
