#!/usr/bin/env python3
helptext = """
Example Options:
  data.npy
  data.npy -i w h
  data.npy -i i c w h
  data.npy -i i c ...       # will automatically pick w, h
  data.npy -i i             # will automatically pick c, w, h
  data.npy -i c w h100:200
  data.npy -i i10:20 w h c

Index specs for -i are given for each axis in order.
They can be any of:
- "i" marks the interactive axis. Example: "i" or as prefix: "i10:20".
- Prefix "w" or "h" marks width or height axis. Example: "w", "h", "w0:100", etc.
- Optional "c" marks a color axis. Can be "c", "c:...", etc.
- Single integer -> constant index for that axis.
- numpy-like slices with ":", e.g. ":", "10:100", "0:100:2".
- Comma-separated list "2,5,7" selects those indices (order is kept).
  Can optionally be wrapped in "()" or "[]" without effect on behavior.
- "..." fills remaining axes with ":".

If no "w" or "h" is given, the two largest remaining axes are used as (w,h),\
with w being the larger of the two.
If no "c" is given, all remaining axes except (w,h) are treated as color axes.

Colors are computed as follows:
- 1 color dimension (X): greyscale, i.e. (R, G, B) = (X, X, X)
- 2 color dimensions (X, Y): yellow-blue, i.e. (R, G, B) = (X, X, Y)
- 3 color dimensions (X, Y, Z): simple color (R, G, B) = (X, Y, Z)
- 4 or more color dimensions: reduced to 3 via PCA across the color axes of the displayed frame.

Interactive Controls:
- Left/Down: previous index on the "i" axis
- Right/Up: next index on the "i" axis
- "0": reset to initial index
- "q" or "escape": close
"""


def parse_cli():
    import argparse

    p = argparse.ArgumentParser(description="Render a slice of a .npy array as an image.",
                                epilog=helptext,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("npy_path", help=".npy file path")
    p.add_argument("-i", "--index", nargs="*", default=[],
                   help="Index specs for each axis. See explanation below.")
    p.add_argument("-s", "--start", type=int, default=None,
                   help="Start index for the interactive axis.")
    args = p.parse_args()


    from .main import main
    main(args)


if __name__ == "__main__":
    parse_cli()

