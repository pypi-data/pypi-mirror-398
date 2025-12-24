#!/usr/bin/env python3
#
# rm68kd - server process

import sys
import argparse
import logging

from .service import create_service


# ----- main -----
def main():
    # parse args
    parser = argparse.ArgumentParser(
        prog="rm68kd", description="rpyc server for the machine68k"
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=18861,
        help="set port of server",
    )
    parser.add_argument(
        "-H",
        "--host",
        default="localhost",
        help="set port of server",
    )
    args = parser.parse_args()

    FORMAT = "%(relativeCreated).0f  %(name)020s  %(levelname)8s  %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logging.info("hallo")

    # main loop
    print("Welcome to rm68kd!")
    print(f"Listening on rpyc {args.host}:{args.port}")
    srv = create_service(
        port=args.port,
        host=args.host,
        type="forking",
    )
    srv.start()


if __name__ == "__main__":
    main()
