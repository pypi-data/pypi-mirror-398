# zz-scripts/chapter03/utils/convert_jalons.py
import argparse
from pathlib import Path

import pandas as pd


def main():
    p = argparse.ArgumentParser(
        description="Extract raw CSV from enriched milestones file"
    )
    p.add_argument(
        "--src", required=True, help="Path to 03_ricci_fR_milestones_enriched.csv"
    )
    p.add_argument(
        "--dst",
        default="zz-data/chapter03/03_ricci_fR_milestones.csv",
        help="Output path for the raw CSV",
    )
    args = p.parse_args()

    src_path = Path(args.src)
    if not src_path.exists():
        print(f"Error: source file not found: {src_path}")
        return

    df = pd.read_csv(src_path)
    df[["R_over_R0", "f_R", "f_RR"]].to_csv(args.dst, index=False)
    print(f"Raw file generated: {args.dst}")


if __name__ == "__main__":
    main()
