from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
from rembg import remove, new_session

ROOT = Path(".")
OUT_PRODUCTS = ROOT / "assets" / "products"
OUT_PROMOS = ROOT / "assets" / "promos"
OUT_PRODUCTS.mkdir(parents=True, exist_ok=True)
OUT_PROMOS.mkdir(parents=True, exist_ok=True)

PRODUCT_FILES = [
    "FB_IMG_1792672226538.jpg",
    "FB_IMG_1792672234943.jpg",
    "FB_IMG_1792672238432.jpg",
    "FB_IMG_1792672241645.jpg",
    "FB_IMG_1792672296313.jpg",
    "FB_IMG_1792672309875.jpg",
    "FB_IMG_1792672321265.jpg",
    "FB_IMG_1792672328540.jpg",
    "FB_IMG_1792672335549.jpg",
    "FB_IMG_1792672802220.jpg",
    "FB_IMG_1792672804458.jpg",
    "FB_IMG_1792672806551.jpg",
    "FB_IMG_1792672808867.jpg",
    "FB_IMG_1792672812749.jpg",
    "FB_IMG_1792672815118.jpg",
]
PROMOS = {
    "FB_IMG_1792672185080.jpg": "offer-50-percent.jpg",
    "FB_IMG_1792672202728.jpg": "offer-buy-3-get-1.jpg",
}

def vivid_rgb(img):
    img = ImageEnhance.Color(img).enhance(1.16)
    img = ImageEnhance.Contrast(img).enhance(1.10)
    img = ImageEnhance.Brightness(img).enhance(1.035)
    return ImageEnhance.Sharpness(img).enhance(1.18)

def fit_on_square(img, size=1000):
    img = ImageOps.exif_transpose(img).convert("RGBA")
    alpha = img.getchannel("A")
    # Remove very faint segmentation haze while preserving soft edges.
    alpha = alpha.point(lambda v: 0 if v < 8 else v)
    img.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox:
        left, top, right, bottom = bbox
        pad = max(12, int(max(right-left, bottom-top) * 0.035))
        bbox = (max(0, left-pad), max(0, top-pad),
                min(img.width, right+pad), min(img.height, bottom+pad))
        img = img.crop(bbox)
    rgb = vivid_rgb(img.convert("RGB"))
    img = Image.merge("RGBA", (*rgb.split(), img.getchannel("A")))
    img.thumbnail((900, 900), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((size-img.width)//2, (size-img.height)//2))
    return canvas

def process_logo():
    src = Image.open("لوجو.jpg")
    src = ImageOps.exif_transpose(src).convert("RGB")
    # Make the white paper transparent while retaining anti-aliased logo strokes.
    gray = ImageOps.grayscale(src)
    alpha = gray.point(lambda v: 255 if v < 45 else (0 if v > 247 else int((247-v)*255/202)))
    # Keep the original mark and lettering; recolor the ink to silver-white for the dark header.
    ink = Image.new("RGBA", src.size, (236, 242, 245, 255))
    ink.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox:
        l, t, r, b = bbox
        pad = 22
        ink = ink.crop((max(0,l-pad), max(0,t-pad), min(ink.width,r+pad), min(ink.height,b+pad)))
    ink.thumbnail((700,700), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (720,720), (0,0,0,0))
    canvas.alpha_composite(ink, ((720-ink.width)//2,(720-ink.height)//2))
    canvas.save(ROOT/"assets"/"shield-logo.png", optimize=True)
    # Also preserve a dark-ink transparent version of the same original artwork.
    dark = Image.new("RGBA", src.size, (17, 25, 29, 255))
    dark.putalpha(alpha)
    if bbox:
        dark = dark.crop((max(0,l-pad), max(0,t-pad), min(dark.width,r+pad), min(dark.height,b+pad)))
    dark.thumbnail((700,700), Image.Resampling.LANCZOS)
    dark_canvas = Image.new("RGBA", (720,720), (0,0,0,0))
    dark_canvas.alpha_composite(dark, ((720-dark.width)//2,(720-dark.height)//2))
    dark_canvas.save(ROOT/"assets"/"shield-logo-original-ink.png", optimize=True)

def main():
    session = new_session("u2net")
    for name in PRODUCT_FILES:
        source = ROOT / name
        if not source.exists():
            raise FileNotFoundError(f"Missing original product image: {source}")
        with Image.open(source) as im:
            im = ImageOps.exif_transpose(im).convert("RGBA")
            cutout = remove(im, session=session)
            if not isinstance(cutout, Image.Image):
                from io import BytesIO
                cutout = Image.open(BytesIO(cutout)).convert("RGBA")
            cutout = fit_on_square(cutout)
            destination = OUT_PRODUCTS / (Path(name).stem + ".png")
            cutout.save(destination, optimize=True)
            print(f"Created {destination} ({destination.stat().st_size:,} bytes)")

    for source_name, dest_name in PROMOS.items():
        with Image.open(ROOT / source_name) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im = vivid_rgb(im)
            im.save(OUT_PROMOS / dest_name, quality=93, optimize=True)
            print(f"Enhanced {OUT_PROMOS / dest_name}")

    process_logo()
    print("Created transparent logo variants.")

if __name__ == "__main__":
    main()
