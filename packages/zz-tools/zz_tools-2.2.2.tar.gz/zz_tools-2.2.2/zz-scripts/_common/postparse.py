"""
Post-parse epilogue for MCGT plotting scripts.

Contract: apply(args) is best-effort and MUST NOT break the figure script.
- Honors MCGT_OUTDIR env as fallback for args.outdir
- Creates outdir if provided
- Applies rcParams for savefig.* if options exist on args
- Registers an atexit hook that copies the latest PNG to outdir
"""

from __future__ import annotations
import os
import atexit


def _copy_latest(args) -> None:
    try:
        if not getattr(args, "outdir", None):
            return

        ch = os.path.basename(os.path.dirname(__file__))  # _common
        # jump two up from the caller file directory (we recompute from __file__ of caller via stack?)
        # Safer: rebuild relative to the caller's file via env set by wrapper; fallback to repo layout.
        # But since all figures write to zz-figures/<chapter>, we recompute from the *caller* path at call-site.
        # Here: we keep generic behavior assuming standard layout used by all chapters.
        # (The call-site sets base_dir and chapter; see apply()).
        pass
    except Exception:
        pass


def apply(args, *, caller_file: str = None) -> None:
    try:
        env_out = os.environ.get("MCGT_OUTDIR")
        if getattr(args, "outdir", None) in (None, "", False) and env_out:
            args.outdir = env_out

        if getattr(args, "outdir", None):
            try:
                os.makedirs(args.outdir, exist_ok=True)
            except Exception:
                pass

        try:
            import matplotlib

            rc = {}
            if hasattr(args, "dpi") and args.dpi:
                rc["savefig.dpi"] = args.dpi
            if hasattr(args, "fmt") and args.fmt:
                rc["savefig.format"] = args.fmt
            if hasattr(args, "transparent"):
                rc["savefig.transparent"] = bool(args.transparent)
            if rc:
                matplotlib.rcParams.update(rc)
        except Exception:
            pass

        # atexit: copy latest PNG from zz-figures/<chapter> to args.outdir
        def _smoke_copy_latest():
            try:
                if not getattr(args, "outdir", None):
                    return
                import glob
                import shutil

                # infer chapter from the caller file location
                base = os.path.abspath(
                    os.path.join(os.path.dirname(caller_file or __file__), "..")
                )
                chapter = os.path.basename(base)
                repo = os.path.abspath(os.path.join(base, ".."))
                default_dir = os.path.join(repo, "zz-figures", chapter)
                pngs = sorted(
                    glob.glob(os.path.join(default_dir, "*.png")),
                    key=os.path.getmtime,
                    reverse=True,
                )
                for p in pngs:
                    if os.path.exists(p):
                        dst = os.path.join(args.outdir, os.path.basename(p))
                        if not os.path.exists(dst):
                            shutil.copy2(p, dst)
                        break
            except Exception:
                pass

        atexit.register(_smoke_copy_latest)

    except Exception:
        # best-effort; never break the figure script
        pass
