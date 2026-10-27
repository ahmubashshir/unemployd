"""A tool for indexing/merging OCI-layout tars."""
from argparse import ArgumentParser
from . import index
from . import merge

cmd = {
    'index': index,
    'merge': merge,
}


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="oci", description=__doc__)

    sps = parser.add_subparsers(dest="command", required=True)

    for name, module in cmd.items():
        sp = sps.add_parser(name, help=module.__doc__)
        module.build_parser(sp)
        validator = getattr(module, "validate_args", None)
        sp.set_defaults(
            handler=module.run,
            cmdparser=sp,
            validate=validator if callable(validator) else None,
        )
    return parser


def main():
    args = build_parser().parse_args()
    if args.validate:
        args.validate(args.cmdparser, args)

    raise SystemExit(args.handler(args) or 0)

# vim: ft=python3:ts=4:et:
