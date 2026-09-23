"""Generate original, reusable raster artwork used in social previews."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site" / "assets"
LOGO_SOURCE = ROOT / "Black White Bold Minimal Creative Agency Logo.png"
INK = "#182820"
PAPER = "#e9e8df"
ORANGE = "#ff6544"
ACID = "#dfff42"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


def cropped_logo() -> Image.Image:
    """Return the uploaded mark with its original artwork and a tight white margin."""
    image = Image.open(LOGO_SOURCE).convert("RGB")
    white = Image.new("RGB", image.size, "white")
    difference = ImageChops.difference(image, white).convert("L")
    bounds = difference.point(lambda value: 255 if value > 24 else 0).getbbox()
    if bounds:
        image = image.crop(bounds)
    side = max(image.size)
    canvas = Image.new("RGB", (side, side), "white")
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def favicon() -> None:
    source = cropped_logo()
    dark = (24, 40, 32)
    white = (244, 242, 232)
    orange = (255, 101, 68)
    pixels = source.load()
    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = pixels[x, y]
            if red > 150 and green < 180 and blue < 155 and red > green * 1.2:
                coverage = max(0.0, min(1.0, (255 - green) / (255 - orange[1])))
                pixels[x, y] = tuple(round(dark[i] * (1 - coverage) + orange[i] * coverage) for i in range(3))
            else:
                luminance = (red + green + blue) / 3
                coverage = 1 - luminance / 255
                pixels[x, y] = tuple(round(dark[i] * (1 - coverage) + white[i] * coverage) for i in range(3))
    source.resize((64, 64), Image.Resampling.LANCZOS).save(ASSETS / "mkrting-favicon.png", optimize=True)


def motorcycle() -> None:
    scale = 2
    image = Image.new("RGB", (1200 * scale, 675 * scale), PAPER)
    draw = ImageDraw.Draw(image)

    def line(points: list[tuple[int, int]], color: str = INK, width: int = 9) -> None:
        draw.line([(x * scale, y * scale) for x, y in points], fill=color, width=width * scale, joint="curve")

    def circle(x: int, y: int, radius: int, fill: str, outline: str = INK, width: int = 8) -> None:
        draw.ellipse(((x - radius) * scale, (y - radius) * scale, (x + radius) * scale, (y + radius) * scale), fill=fill, outline=outline, width=width * scale)

    draw.ellipse((-170 * scale, -360 * scale, 690 * scale, 500 * scale), fill=ACID)
    draw.rounded_rectangle((47 * scale, 43 * scale, 1153 * scale, 632 * scale), radius=30 * scale, outline=INK, width=3 * scale)
    draw.text((90 * scale, 78 * scale), "MKR / CAMPAIGN DECODED", fill=INK, font=font(24 * scale))
    draw.text((90 * scale, 132 * scale), "THE INVISIBLE PART", fill=INK, font=font(46 * scale))
    draw.text((90 * scale, 188 * scale), "OF THE RIDE", fill=INK, font=font(46 * scale))
    line([(90, 538), (1120, 538)], width=3)

    circle(390, 479, 100, PAPER, width=15)
    circle(930, 479, 100, PAPER, width=15)
    circle(390, 479, 56, PAPER, width=5)
    circle(930, 479, 56, PAPER, width=5)
    line([(390, 479), (542, 335), (715, 477), (390, 479)], width=13)
    line([(542, 335), (694, 335), (715, 477)], width=13)
    line([(694, 335), (836, 338), (930, 479)], width=13)
    line([(544, 329), (500, 292), (400, 292)], width=15)
    line([(664, 313), (765, 313), (805, 283)], width=15)
    line([(833, 338), (864, 276), (940, 276)], width=12)
    line([(864, 276), (840, 238)], width=10)
    draw.rounded_rectangle((560 * scale, 359 * scale, 672 * scale, 455 * scale), radius=16 * scale, fill=ORANGE, outline=INK, width=7 * scale)
    draw.text((582 * scale, 380 * scale), "4Ah", fill=INK, font=font(30 * scale))
    line([(672, 402), (785, 402), (875, 339)], color=ORANGE, width=8)
    line([(558, 402), (475, 401), (416, 365)], color=ORANGE, width=8)
    circle(957, 271, 15, ORANGE, width=3)


def editorial_canvas(kicker: str, title: str, background: str, accent: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1200, 675), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((38, 38, 1162, 637), radius=28, outline=INK, width=3)
    draw.text((75, 70), kicker, fill=INK, font=font(23))
    draw.text((75, 115), title, fill=INK, font=font(42))
    draw.line((75, 570, 1125, 570), fill=INK, width=3)
    draw.text((75, 590), "MKR / ORIGINAL STRATEGY DIAGRAM", fill=INK, font=font(18))
    draw.ellipse((1068, 584, 1115, 631), fill=accent)
    return image, draw


def flipkart_story() -> None:
    image, draw = editorial_canvas("FLIPKART / BIG BILLION DAYS 2026", "THE SAME DAY. A DIFFERENT OUTCOME.", "#f5e9df", ORANGE)
    draw.rounded_rectangle((85, 255, 485, 485), radius=24, fill="#ffffff", outline=INK, width=3)
    draw.text((115, 285), "01 / REPEAT", fill=INK, font=font(22))
    draw.text((115, 352), "BAD LUCK", fill=INK, font=font(44))
    draw.rounded_rectangle((715, 255, 1115, 485), radius=24, fill=ACID, outline=INK, width=3)
    draw.text((745, 285), "02 / CHANGE", fill=INK, font=font(22))
    draw.text((745, 352), "NEW LUCK", fill=INK, font=font(44))
    draw.line((505, 370, 685, 370), fill=INK, width=12)
    draw.polygon([(685, 370), (645, 345), (645, 395)], fill=INK)
    draw.text((520, 405), "SHOPPING", fill=INK, font=font(19))
    image.save(ASSETS / "flipkart-luck-story.png", optimize=True)


def amazon_story() -> None:
    image, draw = editorial_canvas("AMAZON / GREAT INDIAN FESTIVAL 2026", "THE SALE PROMISE HAS THREE PARTS.", "#e6eff0", "#ffb45a")
    cards = [
        (80, "01", "DEALS", "Reason to look", "#ffffff"),
        (430, "02", "PRIME", "Reason to join", "#ffdbad"),
        (780, "03", "DELIVERY", "Reason to trust", ACID),
    ]
    for x, number, label, detail, fill in cards:
        draw.rounded_rectangle((x, 245, x + 330, 490), radius=22, fill=fill, outline=INK, width=3)
        draw.text((x + 25, 273), number, fill=INK, font=font(26))
        draw.text((x + 25, 340), label, fill=INK, font=font(37))
        draw.text((x + 25, 440), detail, fill=INK, font=font(21, False))
    image.save(ASSETS / "amazon-festival-strategy.png", optimize=True)


def jio_story() -> None:
    image, draw = editorial_canvas("JIO / TENTH ANNIVERSARY OFFER", "ONE RECHARGE. MANY RETURN MOMENTS.", "#e8e9f5", "#8595ff")
    draw.rounded_rectangle((80, 245, 465, 505), radius=26, fill="#ffffff", outline=INK, width=3)
    draw.text((112, 265), "ANNUAL PLAN", fill=INK, font=font(23))
    draw.text((107, 332), "365", fill=INK, font=font(115))
    draw.text((322, 410), "DAYS", fill=INK, font=font(24))
    draw.line((465, 376, 545, 376), fill=INK, width=8)
    draw.polygon([(545, 376), (520, 360), (520, 392)], fill=INK)
    for index in range(12):
        x = 575 + (index % 6) * 92
        y = 258 + (index // 6) * 124
        draw.rounded_rectangle((x, y, x + 72, y + 84), radius=13, fill=ACID if index % 3 == 0 else "#ffffff", outline=INK, width=3)
        draw.text((x + 15, y + 20), f"{index + 1:02d}", fill=INK, font=font(25))
    image.save(ASSETS / "jio-anniversary-bundle.png", optimize=True)


def zomato_story() -> None:
    image, draw = editorial_canvas("ZOMATO / HEALTHY SUBSCRIPTIONS", "FROM ONE ORDER TO A ROUTINE.", "#f4e7e3", "#ff7662")
    for index, day in enumerate(("MON", "TUE", "WED", "THU", "FRI")):
        x = 82 + index * 210
        draw.rounded_rectangle((x, 255, x + 188, 490), radius=20, fill="#ffffff" if index % 2 else ACID, outline=INK, width=3)
        draw.text((x + 19, 278), day, fill=INK, font=font(24))
        draw.rounded_rectangle((x + 17, 345, x + 171, 430), radius=13, fill="#f4e7e3", outline=INK, width=2)
        draw.text((x + 37, 372), "MEAL", fill=INK, font=font(26))
    image.save(ASSETS / "zomato-meal-routine.png", optimize=True)


def linkedin_launch() -> None:
    """Original launch card sized for a LinkedIn Page image post."""
    image = Image.new("RGB", (1200, 627), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((31, 31, 1169, 596), radius=24, outline=INK, width=3)
    draw.text((73, 68), "mkrting", fill=INK, font=font(42))
    dot_x = 73 + draw.textlength("mkrting", font=font(42))
    draw.text((dot_x, 68), ".", fill=ORANGE, font=font(42))
    draw.text((dot_x + draw.textlength(".", font=font(42)), 68), "com", fill=INK, font=font(42))
    draw.text((899, 81), "MKR / 001", fill=INK, font=font(22))
    draw.line((73, 146, 1127, 146), fill=INK, width=3)
    draw.text((73, 185), "MARKETING,", fill=INK, font=font(104))
    draw.text((73, 294), "DECODED", fill=INK, font=font(104))
    decoded_width = draw.textlength("DECODED", font=font(104))
    draw.ellipse((83 + decoded_width, 373, 108 + decoded_width, 398), fill=ORANGE)
    draw.text((77, 474), "The strategy behind the campaign.", fill=INK, font=font(35, False))
    draw.text((77, 543), "INDIA-FIRST  /  WORLD-AWARE", fill=INK, font=font(19))
    image.save(ASSETS / "linkedin-first-post.png", optimize=True)


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    favicon()
    motorcycle()
    flipkart_story()
    amazon_story()
    jio_story()
    zomato_story()
    linkedin_launch()
