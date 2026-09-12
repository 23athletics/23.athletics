#!/usr/bin/env python3
"""Build a 20s Instagram Reel for 23.athletics with 67 meme + TimGiho."""

from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
W, H = 1080, 1920
FPS = 30
DURATION = 20.0
TOTAL = int(DURATION * FPS)

FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/noto/NotoSansDisplay-Regular.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def load_cover(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    src_w, src_h = img.size
    scale = max(W / src_w, H / src_h)
    nw, nh = int(src_w * scale), int(src_h * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    return img.crop((left, top, left + W, top + H))


def zoom_crop(base: Image.Image, progress: float, amount: float = 0.08) -> Image.Image:
    z = 1.0 + amount * progress
    nw, nh = int(W * z), int(H * z)
    scaled = base.resize((nw, nh), Image.Resampling.BILINEAR)
    left = (nw - W) // 2
    top = (nh - H) // 2
    return scaled.crop((left, top, left + W, top + H))


def darken(img: Image.Image, factor: float) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(factor)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    fnt: ImageFont.FreeTypeFont,
    fill=(255, 255, 255),
    stroke_fill=(0, 0, 0),
    stroke_width: int = 0,
    shadow: bool = True,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke_width)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    if shadow:
        draw.text((x + 4, y + 6), text, font=fnt, fill=(0, 0, 0, 180), stroke_width=stroke_width, stroke_fill=(0, 0, 0))
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def paste_logo(canvas: Image.Image, logo: Image.Image, size: int, y: int, opacity: float = 1.0) -> None:
    logo_r = logo.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    if opacity < 1.0:
        alpha = logo_r.split()[-1].point(lambda p: int(p * opacity))
        logo_r.putalpha(alpha)
    x = (W - size) // 2
    canvas.paste(logo_r, (x, y), logo_r)


def scene_progress(t: float, start: float, end: float) -> float:
    if t <= start:
        return 0.0
    if t >= end:
        return 1.0
    return (t - start) / (end - start)


def render_frame(t: float, assets: dict) -> Image.Image:
    """Timeline:
    0.0-3.5   Logo + brand intro
    3.5-8.5   67 meme explosion
    8.5-14.0  TimGiho shoutout
    14.0-17.5 Fitness CTA
    17.5-20.0 Logo outro / follow
    """
    if t < 3.5:
        return render_intro(t, assets)
    if t < 8.5:
        return render_67(t - 3.5, assets)
    if t < 14.0:
        return render_timgioh(t - 8.5, assets)
    if t < 17.5:
        return render_cta(t - 14.0, assets)
    return render_outro(t - 17.5, assets)


def render_intro(t: float, assets: dict) -> Image.Image:
    p = scene_progress(t, 0, 3.5)
    bg = zoom_crop(assets["gym"], p, 0.06)
    bg = darken(bg, 0.45)
    canvas = bg.convert("RGBA")

    logo_p = ease_out_cubic(scene_progress(t, 0.15, 1.1))
    logo_size = int(280 + 40 * (1 - logo_p))
    logo_y = int(420 + (1 - logo_p) * 80)
    paste_logo(canvas, assets["logo"], logo_size, logo_y, opacity=logo_p)

    draw = ImageDraw.Draw(canvas)
    brand_p = ease_out_cubic(scene_progress(t, 0.7, 1.6))
    if brand_p > 0:
        y = int(760 + (1 - brand_p) * 40)
        draw_centered_text(draw, "23.athletics", y, font(FONT_BOLD, 72), fill=(255, 255, 255), stroke_width=2)

    line_p = ease_out_cubic(scene_progress(t, 1.3, 2.2))
    if line_p > 0:
        y = int(860 + (1 - line_p) * 30)
        draw_centered_text(draw, "Dein Ziel. Dein Plan.", y, font(FONT_REG, 42), fill=(180, 255, 120))

    pulse = 0.5 + 0.5 * math.sin(t * 6)
    if t > 2.4:
        draw_centered_text(draw, "LOS GEHT'S", int(1500 + pulse * 8), font(FONT_BOLD, 36), fill=(255, 255, 255))

    return canvas.convert("RGB")


def render_67(t: float, assets: dict) -> Image.Image:
    p = scene_progress(t, 0, 5.0)
    bg = zoom_crop(assets["meme"], p, 0.12)
    bg = darken(bg, 0.55)
    # flash on beat-ish moments
    flash = max(0.0, 1.0 - abs(t - 0.35) * 8) + max(0.0, 1.0 - abs(t - 2.0) * 8)
    if flash > 0:
        overlay = Image.new("RGB", (W, H), (200, 255, 120))
        bg = Image.blend(bg, overlay, min(0.35, flash * 0.35))

    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Big 6 and 7 with seesaw motion
    swing = math.sin(t * 5.5) * 55
    scale_pop = 1.0 + 0.18 * ease_out_cubic(scene_progress(t, 0.0, 0.45))
    six_size = int(320 * scale_pop)
    seven_size = int(320 * scale_pop)
    f6 = font(FONT_BOLD, six_size)
    f7 = font(FONT_BOLD, seven_size)

    # "6"
    b6 = draw.textbbox((0, 0), "6", font=f6)
    x6 = int(140 + swing)
    y6 = int(520 - swing * 0.35)
    draw.text((x6 + 6, y6 + 8), "6", font=f6, fill=(0, 0, 0))
    draw.text((x6, y6), "6", font=f6, fill=(255, 255, 255), stroke_width=10, stroke_fill=(0, 0, 0))

    # "7"
    b7 = draw.textbbox((0, 0), "7", font=f7)
    x7 = int(620 - swing)
    y7 = int(520 + swing * 0.35)
    draw.text((x7 + 6, y7 + 8), "7", font=f7, fill=(0, 0, 0))
    draw.text((x7, y7), "7", font=f7, fill=(180, 255, 80), stroke_width=10, stroke_fill=(0, 0, 0))

    phrase_p = ease_out_cubic(scene_progress(t, 0.6, 1.3))
    if phrase_p > 0:
        draw_centered_text(
            draw,
            "SIX  ·  SEVEN",
            int(980 + (1 - phrase_p) * 50),
            font(FONT_BOLD, 64),
            fill=(255, 255, 255),
            stroke_width=4,
        )

    sub_p = ease_out_cubic(scene_progress(t, 1.5, 2.3))
    if sub_p > 0:
        draw_centered_text(
            draw,
            "Das Meme. Der Vibe. Die Energie.",
            int(1100 + (1 - sub_p) * 40),
            font(FONT_REG, 36),
            fill=(210, 255, 180),
        )

    tag_p = ease_out_cubic(scene_progress(t, 2.8, 3.6))
    if tag_p > 0:
        draw_centered_text(
            draw,
            "brainrot → gains",
            int(1450 + (1 - tag_p) * 30),
            font(FONT_BOLD, 40),
            fill=(255, 255, 255),
        )

    return canvas.convert("RGB")


def render_timgioh(t: float, assets: dict) -> Image.Image:
    p = scene_progress(t, 0, 5.5)
    bg = zoom_crop(assets["tim"], p, 0.08)
    bg = darken(bg, 0.5)
    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Accent bar
    bar_p = ease_out_cubic(scene_progress(t, 0.1, 0.8))
    if bar_p > 0:
        bar_w = int(W * 0.72 * bar_p)
        x0 = (W - bar_w) // 2
        draw.rounded_rectangle([x0, 430, x0 + bar_w, 438], radius=4, fill=(255, 60, 160))

    title_p = ease_out_cubic(scene_progress(t, 0.2, 1.0))
    if title_p > 0:
        draw_centered_text(
            draw,
            "FEATURING",
            int(460 + (1 - title_p) * 30),
            font(FONT_REG, 34),
            fill=(220, 200, 255),
        )

    name_p = ease_out_cubic(scene_progress(t, 0.45, 1.3))
    if name_p > 0:
        # slight bounce
        bounce = abs(math.sin(t * 3.2)) * 6 * name_p
        draw_centered_text(
            draw,
            "TimGiho",
            int(520 + (1 - name_p) * 60 - bounce),
            font(FONT_BOLD, 120),
            fill=(255, 255, 255),
            stroke_width=6,
        )

    handle_p = ease_out_cubic(scene_progress(t, 1.1, 1.9))
    if handle_p > 0:
        draw_centered_text(
            draw,
            "@timgioh",
            int(680 + (1 - handle_p) * 30),
            font(FONT_BOLD, 52),
            fill=(255, 120, 220),
        )

    line_p = ease_out_cubic(scene_progress(t, 2.0, 2.8))
    if line_p > 0:
        draw_centered_text(
            draw,
            "Monte man yes?",
            int(900 + (1 - line_p) * 40),
            font(FONT_SERIF, 48),
            fill=(255, 255, 255),
        )

    punch_p = ease_out_cubic(scene_progress(t, 2.8, 3.5))
    if punch_p > 0:
        draw_centered_text(
            draw,
            "Wir sagen: 6 7",
            int(980 + (1 - punch_p) * 35),
            font(FONT_BOLD, 56),
            fill=(180, 255, 80),
            stroke_width=3,
        )

    collab_p = ease_out_cubic(scene_progress(t, 4.0, 4.8))
    if collab_p > 0:
        draw_centered_text(
            draw,
            "23.athletics  ×  TimGiho",
            int(1500 + (1 - collab_p) * 25),
            font(FONT_BOLD, 38),
            fill=(255, 255, 255),
        )

    return canvas.convert("RGB")


def render_cta(t: float, assets: dict) -> Image.Image:
    p = scene_progress(t, 0, 3.5)
    bg = zoom_crop(assets["gym"], 0.4 + 0.6 * p, 0.1)
    bg = darken(bg, 0.42)
    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    p1 = ease_out_cubic(scene_progress(t, 0.1, 0.9))
    if p1 > 0:
        draw_centered_text(
            draw,
            "TRAIN HARD.",
            int(620 + (1 - p1) * 50),
            font(FONT_BOLD, 78),
            fill=(255, 255, 255),
            stroke_width=4,
        )

    p2 = ease_out_cubic(scene_progress(t, 0.7, 1.5))
    if p2 > 0:
        draw_centered_text(
            draw,
            "MEME HARDER.",
            int(740 + (1 - p2) * 40),
            font(FONT_BOLD, 78),
            fill=(180, 255, 80),
            stroke_width=4,
        )

    p3 = ease_out_cubic(scene_progress(t, 1.6, 2.4))
    if p3 > 0:
        draw_centered_text(
            draw,
            "Individuelle Pläne. Echte Results.",
            int(980 + (1 - p3) * 30),
            font(FONT_REG, 36),
            fill=(230, 230, 230),
        )

    # floating 67 accent
    float_y = int(1280 + math.sin(t * 4) * 18)
    draw_centered_text(draw, "6 7", float_y, font(FONT_BOLD, 64), fill=(255, 255, 255, 200))

    return canvas.convert("RGB")


def render_outro(t: float, assets: dict) -> Image.Image:
    p = scene_progress(t, 0, 2.5)
    bg = Image.new("RGB", (W, H), (8, 14, 28))
    # subtle vignette from gym
    soft = darken(zoom_crop(assets["gym"], 0.9, 0.02), 0.25)
    bg = Image.blend(bg, soft, 0.55)
    canvas = bg.convert("RGBA")

    logo_p = ease_out_cubic(scene_progress(t, 0.05, 0.7))
    paste_logo(canvas, assets["logo"], int(320 + 20 * (1 - logo_p)), 520, opacity=logo_p)

    draw = ImageDraw.Draw(canvas)
    if ease_out_cubic(scene_progress(t, 0.5, 1.1)) > 0:
        draw_centered_text(draw, "23.athletics", 880, font(FONT_BOLD, 64), fill=(255, 255, 255))

    follow_p = ease_out_cubic(scene_progress(t, 1.0, 1.7))
    if follow_p > 0:
        pulse = 1.0 + 0.04 * math.sin(t * 10)
        draw_centered_text(
            draw,
            "Folge jetzt",
            int(1000 + (1 - follow_p) * 20),
            font(FONT_REG, int(40 * pulse)),
            fill=(180, 255, 120),
        )
        draw_centered_text(
            draw,
            "Link in Bio",
            int(1080 + (1 - follow_p) * 20),
            font(FONT_BOLD, 48),
            fill=(255, 255, 255),
        )

    if t > 1.8:
        draw_centered_text(draw, "6 7  ·  TimGiho approved", 1500, font(FONT_REG, 32), fill=(200, 200, 220))

    return canvas.convert("RGB")


def make_music(path: Path) -> None:
    """Original royalty-free trap-ish beat via ffmpeg synth (no copyrighted samples)."""
    # Kick + clap + bass pulse + hihat noise, ~95 BPM energy for meme reels
    # Filtergraph generates a punchy 20s bed.
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=55:sample_rate=44100:duration=20",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=110:sample_rate=44100:duration=20",
        "-f",
        "lavfi",
        "-i",
        "anoisesrc=color=white:sample_rate=44100:duration=20",
        "-filter_complex",
        (
            # bass sidechain-ish gated pulse every ~0.63s (95bpm)
            "[0:a]volume=0.55,lowpass=f=120,"
            "afade=t=in:st=0:d=0.05,"
            "volume='0.2+0.8*between(mod(t\\,0.632)\\,0\\,0.08)':eval=frame[bass];"
            # mid stab
            "[1:a]volume=0.18,highpass=f=200,lowpass=f=800,"
            "volume='0.15+0.85*between(mod(t+0.316\\,0.632)\\,0\\,0.05)':eval=frame[mid];"
            # hats
            "[2:a]highpass=f=6000,volume=0.07,"
            "volume='0.2+0.8*between(mod(t\\,0.158)\\,0\\,0.02)':eval=frame[hat];"
            # riser into 67 drop (~3.5s) and outro fade
            "[bass][mid][hat]amix=inputs=3:normalize=0,"
            "acompressor=threshold=-18dB:ratio=4:attack=5:release=80,"
            "volume=1.35,"
            "afade=t=in:st=0:d=0.4,"
            "afade=t=out:st=18.5:d=1.5"
        ),
        "-ac",
        "2",
        "-ar",
        "44100",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def encode_video(frames_dir: Path, music: Path, out_mp4: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames_dir / "frame_%04d.jpg"),
        "-i",
        str(music),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        "-r",
        str(FPS),
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frames_dir = OUTPUT / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    print("Loading assets...")
    assets = {
        "logo": Image.open(ASSETS / "logo_23_athletics.png").convert("RGBA"),
        "gym": load_cover(ASSETS / "bg_gym.png"),
        "meme": load_cover(ASSETS / "bg_67_meme.png"),
        "tim": load_cover(ASSETS / "bg_timgioh.png"),
    }

    print(f"Rendering {TOTAL} frames...")
    for i in range(TOTAL):
        t = i / FPS
        frame = render_frame(t, assets)
        frame.save(frames_dir / f"frame_{i:04d}.jpg", quality=92, optimize=True)
        if i % 60 == 0:
            print(f"  {i}/{TOTAL} ({t:.1f}s)")

    music = OUTPUT / "beat.wav"
    print("Generating music...")
    make_music(music)

    out_mp4 = OUTPUT / "23athletics_67_timgioh_reel.mp4"
    print("Encoding MP4...")
    encode_video(frames_dir, music, out_mp4)

    # Also copy a preview stills set
    for name, idx in [("preview_intro.jpg", 45), ("preview_67.jpg", 150), ("preview_timgioh.jpg", 300), ("preview_outro.jpg", 570)]:
        src = frames_dir / f"frame_{idx:04d}.jpg"
        if src.exists():
            Image.open(src).save(OUTPUT / name, quality=90)

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-show_entries",
            "stream=codec_type,width,height,avg_frame_rate",
            "-of",
            "json",
            str(out_mp4),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print(probe.stdout)
    print(f"Done: {out_mp4}")


if __name__ == "__main__":
    main()
