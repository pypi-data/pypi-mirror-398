import os.path
import sys

try:
    from yori.yori_aggregate import aggregate
except ImportError:
    from ..yori_aggregate import aggregate

from importlib.metadata import distribution

VERSION = distribution("yori").version


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Command to aggregate gridded files " + "produced with yori-grid"
    )
    parser.add_argument(
        "--daily",
        metavar="YYYY-mm-dd",
        default="",
        help="Indicate date for daily aggregation",
    )
    parser.add_argument(
        "--method",
        default="",
        help="Choose between C6 Aqua and Terra definition of day, "
        + '"c6aqua" and "c6terra" respectively',
    )
    parser.add_argument(
        "-V",
        "--verbose",
        action="store_true",
        help="Enable verbose mode. Print on screen the list of files "
        + "while they are being processed",
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
    parser.add_argument("output", help="output file name and path")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force yori-aggr to ignore the daily flag in the input "
        + "files. It should be used with caution",
    )
    parser.add_argument(
        "-c",
        "--compression",
        default=5,
        help="set the compression level for the output file (valid " + "range 1-9)",
    )
    parser.add_argument(
        "--min-pixel-counts",
        help="set the minimum number of pixels "
        + "for a grid cell to be included in the output D3 file",
        action="store_true",
    )
    parser.add_argument(
        "--min-valid-days",
        help="set the minimum number of days with "
        + "non zero pixel counts in a grid cell in order to be included "
        + "in the M3 product",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        help="set batch size for the aggregation "
        + "process. Larger batch size can increase speed but requires "
        + "more memory. Default is 2, it should be changed with caution.",
        default=2,
    )
    parser.add_argument(
        "-F",
        "--final",
        help="Create final version of L3 file. All quantities "
        + "used to propagate statistics are deleted (i.e. sum, sum_squares, "
        + "... CAUTION: This operation is irreversible and finalized files "
        + "cannot be processed by Yori anymore",
        action="store_true",
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

    aggregate(
        inputs,
        args.output,
        verbose=args.verbose,
        daily=args.daily,
        satellite=args.method,
        force=args.force,
        compression=args.compression,
        use_min_pixel_counts=args.min_pixel_counts,
        use_min_valid_days=args.min_valid_days,
        batch_size=int(args.batch_size),
        final=args.final,
    )


if __name__ == "__main__":
    main()
