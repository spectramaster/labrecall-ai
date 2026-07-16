"""Build the deterministic, judge-ready LabRecall submission video.

The export intentionally uses only verified screenshots and repository assets. It
does not synthesize sponsor logos, runtime claims, metrics, or product behavior.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
OUT = ROOT / "submission_assets"
WORK = OUT / "video-build"
WIDTH = 1920
HEIGHT = 1080
FPS = 30


@dataclass(frozen=True)
class Scene:
    slug: str
    eyebrow: str
    title: str
    caption: str
    narration: str
    image: Path
    full_bleed: bool = False


SCENES = (
    Scene(
        "01-hook",
        "COCKROACHDB × AWS · AGENTIC MEMORY",
        "Stop solving the same research failure twice.",
        "LabRecall learns only from human-confirmed outcomes.",
        "Research teams lose hours solving the same pipeline failure twice. "
        "LabRecall is an agent that remembers only the repairs people confirmed "
        "actually worked. The memory, not the chat transcript, is the product.",
        ASSETS / "labrecall-cover.png",
        True,
    ),
    Scene(
        "02-live-demo",
        "PUBLIC HTTPS DEMO · SYNTHETIC DATA ONLY",
        "A fresh, isolated proof in one click",
        "Cold incident  /  human confirmation  /  cited recall",
        "This public Amazon Lightsail deployment runs a fresh, session-isolated "
        "proof. It captures a synthetic failure, records an observed outcome, and "
        "then submits a paraphrased repeat so we can see whether memory changes the decision.",
        ASSETS / "video" / "01-home.png",
    ),
    Scene(
        "03-cold",
        "STEP 1 · EPISODIC MEMORY",
        "Cold start: the agent abstains",
        "No confirmed analogue means bounded diagnostics, not invented certainty.",
        "On the first incident, CockroachDB stores the bounded environment and "
        "observations. With no confirmed analogue, LabRecall abstains from claiming "
        "a remembered repair and proposes safe, read-only diagnostics.",
        ASSETS / "video" / "02-proof-cold.png",
    ),
    Scene(
        "04-gated-learning",
        "STEP 2 · OUTCOME MEMORY",
        "Model text is never promoted as truth",
        "Only an observed, human-confirmed success becomes reusable memory.",
        "A repair is not learned from model text. Only an observed, human-confirmed "
        "outcome can promote it into semantic memory, atomically with its provenance "
        "and governance events. The proof finishes with two incidents, one outcome, "
        "one reusable memory, and eight audit events.",
        ASSETS / "video" / "03-proof-recall.png",
    ),
    Scene(
        "05-recall",
        "STEP 3 · DISTRIBUTED VECTOR INDEXING",
        "Warm recall cites the proven repair",
        "Similarity 0.784 · confidence 0.667 · decision score 0.523",
        "On the semantically equivalent failure, CockroachDB's distributed vector "
        "index retrieves the proven repair. The recommendation cites the memory ID, "
        "similarity, calibrated outcome confidence, and decision score, so a reviewer "
        "can inspect exactly why experience affected the plan.",
        ASSETS / "video" / "04-evidence.png",
    ),
    Scene(
        "06-governance",
        "COCKROACHDB · ONE CONSISTENCY BOUNDARY",
        "Transactional state and vector memory stay together",
        "Capture, retrieval, recommendation, outcome, and promotion are ordered events.",
        "Incidents, outcomes, repair memories, and governance events share one "
        "transactional source of truth. Namespace isolation prevents public test "
        "sessions from contaminating each other, while least-privilege grants and an "
        "ordered audit trail make every promotion reviewable.",
        ASSETS / "video" / "05-audit.png",
    ),
    Scene(
        "07-architecture",
        "VERIFIED DEPLOYMENT BOUNDARY",
        "Honest failure behavior is part of the design",
        "Lightsail hosts the live service; CockroachDB stores memory and audit evidence.",
        "Amazon Lightsail hosts the bounded FastAPI service behind rate-limited HTTPS, "
        "and its fixed address is the only cloud egress allowed to reach CockroachDB. "
        "Bedrock adapters are implemented, but an account-level Runtime restriction is "
        "under AWS review. The public proof explicitly reports its isolated deterministic "
        "embedding provider instead of pretending a blocked model call succeeded.",
        ASSETS / "labrecall-architecture.png",
    ),
    Scene(
        "08-close",
        "OPEN SOURCE · REPRODUCIBLE · TESTED",
        "Governed memory your next run can trust",
        "github.com/spectramaster/labrecall-ai  ·  https://32.184.180.92",
        "The official CockroachDB Agent Skills repository is pinned as a reproducible "
        "database review gate. Twenty-one automated tests pass. LabRecall turns "
        "troubleshooting into governed organizational memory: evidence, outcomes, "
        "confidence, and a repair your next run can trust.",
        ASSETS / "labrecall-cover.png",
        True,
    ),
)


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size, index=1 if bold else 0)
        except OSError:
            continue
    return ImageFont.load_default()


def contain(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    result = image.copy()
    result.thumbnail(box, Image.Resampling.LANCZOS)
    return result


def cover(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    target_ratio = box[0] / box[1]
    source_ratio = image.width / image.height
    if source_ratio > target_ratio:
        crop_width = round(image.height * target_ratio)
        left = (image.width - crop_width) // 2
        image = image.crop((left, 0, left + crop_width, image.height))
    else:
        crop_height = round(image.width / target_ratio)
        top = (image.height - crop_height) // 2
        image = image.crop((0, top, image.width, top + crop_height))
    return image.resize(box, Image.Resampling.LANCZOS)


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    size: int,
    color: str,
    bold: bool = False,
) -> None:
    draw.text(xy, text, font=font(size, bold), fill=color)


def render_scene(scene: Scene, destination: Path) -> None:
    source = Image.open(scene.image).convert("RGB")
    if scene.full_bleed:
        canvas = cover(source, (WIDTH, HEIGHT)).convert("RGBA")
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        gradient = ImageDraw.Draw(overlay)
        for y in range(HEIGHT):
            alpha = int(190 * (y / HEIGHT) ** 1.7)
            gradient.line((0, y, WIDTH, y), fill=(4, 8, 20, alpha))
        canvas = Image.alpha_composite(canvas, overlay)
        panel_y = 760
    else:
        canvas = Image.new("RGBA", (WIDTH, HEIGHT), "#060914")
        glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((1100, -500, 2300, 700), fill=(30, 219, 180, 38))
        glow_draw.ellipse((-450, 260, 650, 1360), fill=(113, 86, 255, 34))
        canvas = Image.alpha_composite(canvas, glow.filter(ImageFilter.GaussianBlur(80)))
        framed = contain(source, (1660, 720))
        x = (WIDTH - framed.width) // 2
        y = 205 + (700 - framed.height) // 2
        shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (x - 12, y - 12, x + framed.width + 12, y + framed.height + 12),
            radius=30,
            fill=(0, 0, 0, 150),
        )
        canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(18)))
        mask = Image.new("L", framed.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, *framed.size), radius=22, fill=255)
        canvas.paste(framed, (x, y), mask)
        panel_y = 925

    draw = ImageDraw.Draw(canvas)
    if scene.full_bleed:
        draw.rounded_rectangle((70, panel_y, 1850, 1020), radius=28, fill=(4, 8, 20, 220))
        draw_text(draw, (110, panel_y + 28), scene.eyebrow, size=26, color="#6ee7c7", bold=True)
        draw_text(draw, (110, panel_y + 68), scene.title, size=48, color="#ffffff", bold=True)
        draw_text(draw, (110, panel_y + 128), scene.caption, size=25, color="#cbd5e1")
    else:
        draw_text(draw, (130, 70), scene.eyebrow, size=25, color="#6ee7c7", bold=True)
        draw_text(draw, (130, 111), scene.title, size=46, color="#ffffff", bold=True)
        draw.rounded_rectangle((110, panel_y, 1810, 1045), radius=24, fill=(11, 17, 31, 230))
        draw_text(draw, (145, panel_y + 38), scene.caption, size=27, color="#dbeafe", bold=True)

    canvas.convert("RGB").save(destination, quality=95)


def audio_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def build() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("ffmpeg and ffprobe are required")
    if shutil.which("say") is None:
        raise RuntimeError("macOS say is required")

    WORK.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    concat_lines: list[str] = []
    subtitle_blocks: list[str] = []
    timeline = 0.0

    for index, scene in enumerate(SCENES, start=1):
        slide = WORK / f"{index:02d}-{scene.slug}.png"
        audio = WORK / f"{index:02d}-{scene.slug}.aiff"
        segment = WORK / f"{index:02d}-{scene.slug}.mp4"
        render_scene(scene, slide)
        run("say", "-v", "Daniel", "-r", "170", "-o", str(audio), scene.narration)
        duration = audio_duration(audio) + 0.9
        frames = max(1, round(duration * FPS))
        run(
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-i",
            str(slide),
            "-i",
            str(audio),
            "-filter_complex",
            (
                f"[0:v]scale=2048:1152,zoompan=z='min(zoom+0.00018,1.035)'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p[v]"
            ),
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(segment),
        )
        concat_lines.append(f"file '{segment}'")
        manifest.append(
            {
                "scene": scene.slug,
                "start_seconds": round(timeline, 3),
                "duration_seconds": round(duration, 3),
                "source_image": str(scene.image.relative_to(ROOT)),
                "eyebrow": scene.eyebrow,
                "title": scene.title,
                "caption": scene.caption,
                "narration": scene.narration,
            }
        )
        subtitle_text = "\n".join(textwrap.wrap(scene.narration, width=64))
        subtitle_blocks.append(
            f"{index}\n{srt_timestamp(timeline)} --> "
            f"{srt_timestamp(timeline + duration - 0.25)}\n{subtitle_text}\n"
        )
        timeline += duration

    concat = WORK / "concat.txt"
    concat.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
    output = OUT / "labrecall-ai-devpost-demo.mp4"
    run(
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(output),
    )

    thumbnail = cover(Image.open(ASSETS / "labrecall-cover.png").convert("RGB"), (1280, 720))
    thumb_draw = ImageDraw.Draw(thumbnail)
    thumb_draw.rounded_rectangle((40, 580, 1240, 690), radius=24, fill=(4, 8, 20, 220))
    draw_text(
        thumb_draw,
        (75, 602),
        "Outcome-gated memory that learns only from evidence",
        size=38,
        color="#ffffff",
        bold=True,
    )
    thumbnail.save(OUT / "labrecall-ai-youtube-thumbnail.jpg", quality=92, optimize=True)

    devpost_thumbnail = Image.new("RGB", (1200, 800), "#050914")
    devpost_cover = Image.open(ASSETS / "labrecall-cover.png").convert("RGB")
    devpost_cover = devpost_cover.resize((1200, 675), Image.Resampling.LANCZOS)
    devpost_thumbnail.paste(devpost_cover, (0, 0))
    devpost_draw = ImageDraw.Draw(devpost_thumbnail)
    devpost_draw.rounded_rectangle((45, 660, 1155, 770), radius=24, fill=(4, 8, 20, 235))
    draw_text(
        devpost_draw,
        (78, 683),
        "Outcome-gated agentic memory",
        size=46,
        color="#ffffff",
        bold=True,
    )
    devpost_thumbnail.save(OUT / "labrecall-ai-devpost-thumbnail.jpg", quality=92, optimize=True)

    gallery_dir = OUT / "devpost-gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    for scene_index in (2, 4, 5, 6, 7):
        scene = SCENES[scene_index - 1]
        source_slide = WORK / f"{scene_index:02d}-{scene.slug}.png"
        gallery = Image.new("RGB", (1200, 800), "#050914")
        gallery_frame = Image.open(source_slide).convert("RGB")
        gallery_frame = gallery_frame.resize((1200, 675), Image.Resampling.LANCZOS)
        gallery.paste(gallery_frame, (0, 0))
        gallery_draw = ImageDraw.Draw(gallery)
        draw_text(
            gallery_draw,
            (56, 704),
            scene.caption,
            size=31,
            color="#ffffff",
            bold=True,
        )
        gallery.save(
            gallery_dir / f"{scene_index:02d}-{scene.slug}.jpg",
            quality=91,
            optimize=True,
        )

    metadata = {
        "title": "LabRecall AI — Outcome-Gated Agentic Memory with CockroachDB + AWS",
        "published_url": "https://youtu.be/llfCoDkt1DE",
        "description": (
            "LabRecall AI remembers which research-pipeline repairs actually worked and "
            "learns only from human-confirmed outcomes. Built for the CockroachDB × AWS "
            "Build with Agentic Memory Hackathon.\n\n"
            "Live demo: https://32.184.180.92\n"
            "Source: https://github.com/spectramaster/labrecall-ai\n\n"
            "The demo uses synthetic data only. Amazon Lightsail hosts the public service; "
            "CockroachDB provides transactional vector memory and the audit trail. Bedrock "
            "adapters are implemented, while an account-level Runtime restriction is under "
            "AWS review; the public demo reports its isolated deterministic embedding provider."
        ),
        "visibility": "Public",
        "duration_seconds": round(timeline, 3),
        "resolution": f"{WIDTH}x{HEIGHT}",
        "fps": FPS,
        "scenes": manifest,
    }
    (OUT / "labrecall-video-manifest.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUT / "labrecall-ai-en.srt").write_text("\n".join(subtitle_blocks), encoding="utf-8")
    if timeline >= 180:
        raise RuntimeError(f"video is {timeline:.2f}s; Devpost requires under 180s")
    print(json.dumps({"output": str(output), "duration_seconds": round(timeline, 3)}, indent=2))


if __name__ == "__main__":
    build()
