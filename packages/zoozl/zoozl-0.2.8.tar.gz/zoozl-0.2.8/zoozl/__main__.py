"""Zoozl services hub."""

import argparse
import logging
import tomllib

from .server import start


def get_conf(path):
    """Return dict object as configuration."""
    conf = {}
    if path:
        with open(path, "rb") as fname:
            conf = tomllib.load(fname)
    return conf


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zoozl hub of services")
    parser.add_argument(
        "-v",
        action="store_true",
        help="enable verbose debugging mode",
    )
    parser.add_argument(
        "--conf",
        type=str,
        help="path for configuration",
    )
    parser.add_argument(
        "--force-bind",
        action="store_true",
        help="bind to port even if it is already in use",
    )
    args = parser.parse_args()
    if args.v:
        logging.basicConfig(level=10)
    else:
        logging.basicConfig(level=20)
    conf = get_conf(args.conf)
    conf["force_bind"] = args.force_bind
    start(conf)
