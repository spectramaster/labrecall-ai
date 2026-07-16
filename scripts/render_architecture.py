"""Render the public, credential-free LabRecall architecture diagram."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "labrecall-architecture.png"
WIDTH, HEIGHT = 1800, 1050


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}", size)


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    lines: list[str],
    *,
    fill: str,
    outline: str,
    dashed: bool = False,
) -> None:
    draw.rounded_rectangle(xy, radius=20, fill=fill, outline=outline, width=3)
    if dashed:
        x1, y1, x2, y2 = xy
        for x in range(x1 + 18, x2 - 18, 24):
            draw.line((x, y1, min(x + 12, x2), y1), fill="#fb7185", width=5)
            draw.line((x, y2, min(x + 12, x2), y2), fill="#fb7185", width=5)
    x1, y1, _, _ = xy
    draw.text((x1 + 22, y1 + 18), title, font=font(23, bold=True), fill="#f8fafc")
    y = y1 + 58
    for line in lines:
        draw.text((x1 + 22, y), line, font=font(17), fill="#cbd5e1")
        y += 26


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    label: str,
    *,
    color: str = "#94a3b8",
) -> None:
    draw.line((*start, *end), fill=color, width=4)
    ex, ey = end
    sx, sy = start
    if abs(ex - sx) >= abs(ey - sy):
        direction = 1 if ex > sx else -1
        points = [(ex, ey), (ex - 14 * direction, ey - 8), (ex - 14 * direction, ey + 8)]
    else:
        direction = 1 if ey > sy else -1
        points = [(ex, ey), (ex - 8, ey - 14 * direction), (ex + 8, ey - 14 * direction)]
    draw.polygon(points, fill=color)
    if label:
        mx, my = (sx + ex) // 2, (sy + ey) // 2
        bbox = draw.textbbox((0, 0), label, font=font(15, bold=True))
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle(
            (mx - tw // 2 - 7, my - 14, mx + tw // 2 + 7, my + 10), 6, fill="#07111f"
        )
        draw.text((mx - tw // 2, my - 12), label, font=font(15, bold=True), fill="#cbd5e1")


def main() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#07111f")
    draw = ImageDraw.Draw(image)
    draw.text((60, 42), "LabRecall AI", font=font(42, bold=True), fill="#f8fafc")
    draw.text(
        (60, 94),
        "Outcome-gated agentic memory on CockroachDB + AWS",
        font=font(25),
        fill="#94a3b8",
    )

    draw.rounded_rectangle((360, 160, 990, 930), 28, outline="#f59e0b", width=4)
    draw.text((390, 177), "AWS — Amazon Lightsail", font=font(25, bold=True), fill="#fbbf24")
    draw.rounded_rectangle((1050, 160, 1740, 930), 28, outline="#22c55e", width=4)
    draw.text(
        (1080, 177),
        "CockroachDB Cloud — persistent memory",
        font=font(25, bold=True),
        fill="#4ade80",
    )

    box(
        draw,
        (55, 400, 300, 565),
        "Researcher / judge",
        ["Synthetic incident", "Confirmed outcome"],
        fill="#312e81",
        outline="#818cf8",
    )
    box(
        draw,
        (405, 250, 690, 380),
        "Nginx",
        ["Rate limits", "Renewed HTTPS"],
        fill="#3b2a16",
        outline="#f59e0b",
    )
    box(
        draw,
        (735, 250, 945, 405),
        "FastAPI agent",
        ["Bounded diagnostics", "Request IDs", "Safe errors"],
        fill="#1f2937",
        outline="#38bdf8",
    )
    box(
        draw,
        (405, 470, 690, 650),
        "Outcome gate",
        ["Human confirmation", "before promotion", "No command execution"],
        fill="#0f3d36",
        outline="#34d399",
    )
    box(
        draw,
        (735, 500, 945, 655),
        "Active provider",
        ["Deterministic", "1024-D embedding", "Isolated namespace"],
        fill="#243b53",
        outline="#38bdf8",
    )
    box(
        draw,
        (735, 735, 945, 875),
        "Bedrock adapters",
        ["Titan + Nova", "Account review pending"],
        fill="#3b2735",
        outline="#fb7185",
        dashed=True,
    )

    box(
        draw,
        (1095, 250, 1395, 385),
        "Episodic memory",
        ["Incidents", "Environment"],
        fill="#12372a",
        outline="#22c55e",
    )
    box(
        draw,
        (1435, 250, 1695, 385),
        "Outcome memory",
        ["Success / failure", "Side effects"],
        fill="#12372a",
        outline="#22c55e",
    )
    box(
        draw,
        (1095, 485, 1395, 640),
        "Semantic memory",
        ["Promoted repairs", "Calibrated confidence"],
        fill="#12372a",
        outline="#22c55e",
    )
    box(
        draw,
        (1435, 485, 1695, 640),
        "Vector indexes",
        ["Namespace-scoped", "Cosine recall"],
        fill="#164e63",
        outline="#22d3ee",
    )
    box(
        draw,
        (1095, 735, 1395, 875),
        "Governance memory",
        ["Ordered provenance", "Evidence IDs"],
        fill="#12372a",
        outline="#22c55e",
    )
    box(
        draw,
        (1435, 735, 1695, 875),
        "Verified proof",
        ["Cold → confirmed", "Learned recall 0.823063"],
        fill="#312e81",
        outline="#a78bfa",
    )

    arrow(draw, (300, 465), (405, 315), "HTTPS")
    arrow(draw, (690, 315), (735, 315), "proxy")
    arrow(draw, (840, 405), (840, 500), "embed")
    arrow(draw, (690, 560), (1095, 550), "promote")
    arrow(draw, (300, 510), (405, 555), "confirm")
    arrow(draw, (945, 315), (1095, 315), "atomic write")
    arrow(draw, (945, 575), (1435, 560), "vector")
    arrow(draw, (1395, 315), (1435, 315), "outcome")
    arrow(draw, (1395, 560), (1435, 560), "index")
    arrow(draw, (945, 360), (1095, 790), "audit")
    arrow(draw, (1395, 790), (1435, 790), "visible")
    arrow(draw, (840, 735), (840, 655), "blocked", color="#fb7185")

    draw.rounded_rectangle((55, 770, 660, 925), 22, fill="#151f31", outline="#f59e0b", width=3)
    draw.text(
        (80, 790), "Pinned CockroachDB Agent Skills", font=font(23, bold=True), fill="#fbbf24"
    )
    draw.text(
        (80, 832), "Transaction + SQL + cloud-security review gates", font=font(18), fill="#cbd5e1"
    )
    draw.text(
        (80, 866),
        "No credentials, account IDs, or private data in this diagram",
        font=font(17),
        fill="#94a3b8",
    )

    image.save(OUTPUT, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
