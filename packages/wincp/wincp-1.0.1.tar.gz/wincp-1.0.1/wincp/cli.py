import os
import sys
import argparse

from wincp.utils import build_tree_raw, save_archive, load_archive



def cli_main():
    parser = argparse.ArgumentParser(
        description="WinCP CLI – Compress & Extract CMP archives"
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compress")
    c.add_argument("folder")
    c.add_argument("output")
    c.add_argument("--password", default=None)
    c.add_argument("--level", type=int, default=9)
    c.add_argument("--icon", default=None)
    c.add_argument("--icon-enable", action="store_true")

    e = sub.add_parser("extract")
    e.add_argument("cmpfile")
    e.add_argument("dest")
    e.add_argument("--password", default=None)

    try:
        args = parser.parse_args()

        if args.cmd == "compress":
            tree = build_tree_raw(args.folder)
            save_archive(
                tree,
                args.output,
                args.password,
                args.level,
                args.icon,
                args.icon_enable
            )
            print(f"WinCP: Compressed → {args.output}")

        elif args.cmd == "extract":
            archive = load_archive(args.cmpfile, args.password)

            def extract(n, p):
                t = os.path.join(p, n["name"])
                if n["type"] == "dir":
                    os.makedirs(t, exist_ok=True)
                    for c in n.get("children", []):
                        extract(c, t)
                else:
                    with open(t, "wb") as f:
                        f.write(n["content"])

            extract(archive["tree"], args.dest)
            print("WinCP: Extract complete")

    except Exception as e:
        print(f"WinCP Error: {e}")
        sys.exit(1)
