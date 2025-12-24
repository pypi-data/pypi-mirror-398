# zz-scripts/_common/cli.py
def add_common_cli(parser):
    parser.add_argument(
        "--fmt", "--format", dest="fmt", choices=["png", "pdf", "svg"], default=None
    )
    parser.add_argument("--dpi", type=int, default=None)
    parser.add_argument("--outdir", type=str, default=None)
    parser.add_argument("--transparent", action="store_true")
    parser.add_argument(
        "--style", choices=["paper", "talk", "mono", "none"], default="none"
    )
    parser.add_argument("--verbose", action="store_true")
    return parser
