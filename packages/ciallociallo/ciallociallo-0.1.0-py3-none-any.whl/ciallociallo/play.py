#!/usr/bin/env python3
import curses
import time
import base64
import zlib
from importlib import resources as ir
from .check_sysinfo import probe_terminal

PACKAGE = "ciallociallo"

# ---------- 资源路径选择 ----------

def _bundle_path(role, width, aspect):
    return ir.files(PACKAGE).joinpath("txt_frames", role, f"w{width}", f"a{aspect}.cap")

# ---------- 差分包解码 ----------

def _b64u(s: str) -> bytes:
    return zlib.decompress(base64.b64decode(s.encode("ascii")))

def decode_bundle(text: str):
    """
    输入 .cap 文本内容，返回 [frame_text] 列表（每帧一个完整字符串）
    """
    lines = text.splitlines()
    if not lines or not lines[0].startswith("CIALLOPACK v1"):
        raise ValueError("Not a CIALLOPACK v1 file")

    hdr = lines[0].split()
    R, C, N = map(int, hdr[2:5])
    # keyint = int(hdr[5])  # 用不到也可以读一下
    i = 2  # 跳过 ENCODING 行
    frames = []
    current = None

    while i < len(lines):
        tag = lines[i] if i < len(lines) else ""
        if tag.startswith("---K"):
            i += 1
            # 读 R 行关键帧
            buf = []
            for _ in range(R):
                if i >= len(lines):
                    raise ValueError("Truncated keyframe")
                line = lines[i]
                # 保证宽度一致
                if len(line) != C:
                    # 容错：pad 或截断
                    line = (line + " " * C)[:C]
                buf.append(line)
                i += 1
            current = buf
            frames.append("\n".join(current) + "\n")
        elif tag.startswith("---D"):
            # 下两行：mask_b64, chars_b64
            mask_b64 = lines[i + 1] if i + 1 < len(lines) else ""
            chars_b64 = lines[i + 2] if i + 2 < len(lines) else ""
            i += 3
            if current is None:
                raise ValueError("Delta before first keyframe")
            mask = _b64u(mask_b64)
            chars = _b64u(chars_b64).decode("utf-8", errors="replace")

            # 应用差分（线性扫描）
            out = [list(row) for row in current]   # 深拷贝
            Rlen = R * C
            bit_idx = 0
            char_idx = 0
            for byte in mask:
                for b in range(8):
                    if bit_idx >= Rlen:
                        break
                    if (byte >> b) & 1:
                        r = bit_idx // C
                        c = bit_idx % C
                        if char_idx >= len(chars):
                            raise ValueError("Not enough chars in delta")
                        out[r][c] = chars[char_idx]
                        char_idx += 1
                    bit_idx += 1
            # 若 mask 比特不足，剩余位置默认不变；多出的比特被忽略
            current = ["".join(row) for row in out]
            frames.append("\n".join(current) + "\n")
        else:
            i += 1  # 跳过空行或未知行

        if len(frames) >= N:
            break

    if len(frames) != N:
        # 容错：如果包里没标齐，也尽力返回已有帧
        pass
    return frames

# ---------- 居中裁剪 ----------


def slice_center(lines, max_h, max_w):
    content_h = len(lines)
    content_w = max((len(L.rstrip("\n")) for L in lines), default=0)
    h_display = min(content_h, max_h)
    w_display = min(content_w, max_w)
    row_start = 0 if content_h <= max_h else (content_h - max_h) // 2
    col_start = 0 if content_w <= max_w else (content_w - max_w) // 2
    top = (max_h - content_h) // 2 if content_h <= max_h else 0
    left = (max_w - content_w) // 2 if content_w <= max_w else 0
    clipped, end_row = [], row_start + h_display
    for i in range(row_start, end_row):
        raw = lines[i].rstrip("\n") if i < content_h else ""
        padded = raw.ljust(content_w)
        clipped.append(padded[col_start: col_start + w_display])
    return clipped, top, left

# ---------- 播放 ----------


def play(stdscr, frames_texts, fps):
    curses.curs_set(0)
    stdscr.nodelay(True)
    if curses.has_colors():
        curses.start_color()
        try:
            curses.use_default_colors()
        except curses.error:
            pass

    frames = [ft.splitlines() for ft in frames_texts]
    idx, last, delay = 0, 0.0, 1.0 / max(fps, 1e-6)
    while True:
        now = time.time()
        if now - last >= delay:
            last = now
            lines = frames[idx]
            stdscr.erase()
            H, W = stdscr.getmaxyx()
            clipped, top, left = slice_center(lines, H, W)
            for r, line in enumerate(clipped):
                try:
                    stdscr.addstr(top + r, left, line)
                except curses.error:
                    pass
            stdscr.refresh()
            idx = (idx + 1) % len(frames)
        c = stdscr.getch()
        if c != -1:
            break
        time.sleep(0.005)

# ---------- 主流程 ----------


def choose_width(terminfo, aspect, x_ratio=1.0, y_ratio=1.0):
    width = 0
    for i in [70, 80, 90, 100, 110, 120, 130, 140, 150]:
        if i * x_ratio > terminfo['columns'] or i * aspect * y_ratio > terminfo['rows']:
            break
        width = i
    return width


def murasame_width(terminfo, aspect):
    return choose_width(terminfo, aspect, 1.0, 0.65)


def amane_width(terminfo, aspect):
    return choose_width(terminfo, aspect, 0.7, 0.87)


def main(args):
# ---------- who ----------
    who = args.who.lower()

# ---------- terminal & aspect ----------
    terminfo = probe_terminal()
    candidates = [0.3, 0.4, 0.5, 0.55, 0.6, 0.7]
    need_aspect = terminfo['cell_aspect_w_over_h']
    best_aspect = min(candidates, key=lambda a: abs(a - need_aspect))

# ---------- fps & width ----------
    fps = getattr(args, "fps", 36) or 36
    if who.startswith("murasame"):
        width = murasame_width(terminfo, best_aspect)
        fps = 30
    elif who.startswith("amane"):
        width = amane_width(terminfo, best_aspect)
        fps = 30
    elif who.startswith("ririko"):
        width = choose_width(terminfo, best_aspect)
    else:
        width = choose_width(terminfo, best_aspect)

# ---------- oops ----------
    if width == 0:
        raise SystemExit("Ririko: Ahhaha, your terminal is too small or unsupported...")

# ---------- play ----------
    bundle = _bundle_path(who, width, best_aspect)
    frames_texts = None
    with bundle.open("r", encoding="utf-8", errors="ignore") as f:
        frames_texts = decode_bundle(f.read())
    curses.wrapper(lambda stdscr: play(stdscr, frames_texts, fps))
