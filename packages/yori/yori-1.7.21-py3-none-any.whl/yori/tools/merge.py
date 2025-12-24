import os.path
import sys
from importlib.metadata import distribution

# from ..yori_aggregate import aggregate
from ..yori_merge import merge

VERSION = distribution("yori").version


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Command to two gridded files "
        + "produced with either yori-grid or yori-aggr"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION,
        help="Show version and exit",
    )
    parser.add_argument(
        "filelist",
        help="Can be a file path to an input file containing a single "
        + 'input file per line, or "-" to read input list one per line '
        + "from standard input, or a comma separated list of files to "
        + "use as input.",
    )
    parser.add_argument(
        "output",
        help="output file name and path. If --replace is "
        "used, file1 is renamed instead.",
    )
    #    parser.add_argument('-r', '--replace',
    #                        help='merge does not create a new merged file, instead, it add '
    #                             'variables from file2 into file1. If this option is used '
    #                             'the argument "output" renames file1', action='store_true')
    parser.add_argument(
        "-c",
        "--compression",
        default=5,
        help="set the compression level for the output file (valid range 1-9)",
    )
    parser.add_argument(
        "-f",
        "--fill-value",
        help="allows the user to overwrite the fill values in the input files",
    )

    args = parser.parse_args()

    # read file list from stdin
    if args.filelist == "-":
        inputs = [l.strip() for l in sys.stdin.read().split("\n") if l.strip()]

    # if the file exists, assume it is a file and try to fetch inputs
    elif os.path.exists(args.filelist):
        inputs = [
            l.strip() for l in open(args.filelist).read().split("\n") if l.strip()
        ]

    else:
        inputs = [f.strip() for f in args.filelist.split(",")]

    merge(inputs, args.output, compression=args.compression, fill_value=args.fill_value)
