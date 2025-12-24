#!/usr/bin/env python3
#
# rm68k-cli - small client test program

import sys
import argparse
import logging

from .client import create_client


# ----- main -----
def main():
    # parse args
    parser = argparse.ArgumentParser(
        prog="rm68k-cli", description="rpyc client for machine68k"
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
    parser.add_argument(
        "-C",
        "--cpu",
        default="68000",
        help="set CPU type of m68k machine",
    )
    parser.add_argument(
        "-m",
        "--ram-size",
        default=1024,
        type=int,
        help="set RAM size in KiB",
    )
    args = parser.parse_args()

    # main loop
    print("Welcome to rm68k-cli!")
    print(f"Connecting on rpyc {args.host}:{args.port}")
    c = create_client(port=args.port, host=args.host)
    mach = c.create_machine(args.cpu, args.ram_size)

    cpu = mach.cpu
    mem = mach.mem
    traps = mach.traps

    mem.w_block(0, b"hello")
    mem.w_block(0, bytearray(b"hello"))

    print("done")
    c.release_machine()
    c.close()


if __name__ == "__main__":
    main()
