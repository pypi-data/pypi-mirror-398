try:
    from yori.run_yori import callYori
except ImportError:
    from ..run_yori import callYori

from importlib.metadata import distribution

VERSION = distribution("yori").version


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Command for gridding geophysical data"
    )
    # replace debug with verbose in a future version and have a command to print
    # some info when the proper flag is used
    #    parser.add_argument('--debug', action='store_true',
    #                        help='enable debug; for development only!')
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION,
        help="show version and exit",
    )
    parser.add_argument("cfgfile", help="Yori yaml config file")
    parser.add_argument(
        "input", help="name and path of the input file in netcdf4 format"
    )
    parser.add_argument("output", help="name and path of the output gridded file")
    parser.add_argument(
        "-c",
        "--compression",
        default=5,
        help="set the compression level for netcdf4 (0=none 9=max)",
    )

    args = parser.parse_args()

    callYori(args.cfgfile, args.input, args.output, compression=args.compression)


if __name__ == "__main__":
    main()
