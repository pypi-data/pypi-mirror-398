import argparse
from importlib import resources as ir

PACKAGE = "ciallociallo"  # 你的包名

def _available_characters():
    base = ir.files(PACKAGE).joinpath("txt_frames")
    if not base.exists():
        return []
    return sorted([p.name for p in base.iterdir() if p.is_dir()])

def main():
    chars = _available_characters()
    choices_text = f"available: {', '.join(chars)}" if chars else "no roles found"

    ap = argparse.ArgumentParser(
        prog="ciallociallo",
        description="Ciallo~(∠・ω< )⌒★ This is a CLI ASCII animation screensaver.",
        epilog=(
            "examples:\n"
            "  ciallociallo            # defaults to 'ririko'\n"
            "  ciallociallo ririko\n"
            "  ciallociallo murasame\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # 位置参数：角色名（可省略）
    ap.add_argument(
        "who",
        nargs="?",
        metavar="who",
        help=f"character to play (Ciallo~(∠・ω< )⌒★ {choices_text})",
        default="ririko",
    )
    
    args = ap.parse_args()
    
    who = args.who
    if who not in chars:
        raise SystemExit(f"Ririko: Ahhaha, {who} is not supported yet... (available: {', '.join(sorted(chars))})")
    

    # 延迟导入，避免循环依赖
    from .play import main as run_player
    title = f"ciallociallo — {args.who}"
    # 可选：传 reset = None 让 shell 自己恢复；或给一个自定义标题
    from .set_title import terminal_title
    try:
        with terminal_title(title, reset=None):
            run_player(args)
    except KeyboardInterrupt:
        raise SystemExit(0)