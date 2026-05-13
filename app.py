import streamlit as st
from PIL import Image
import io
import math

st.set_page_config(page_title="Photo Layout Maker", page_icon="🖼️", layout="centered")

st.title("🖼️ Photo Layout Maker")
st.caption("อัปโหลดภาพ 1–6 ภาพ แล้วเลือก Layout เพื่อรวมเป็นภาพเดียว")

# --- Sidebar settings ---
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    layout = st.selectbox("เลือก Layout", [
        "สไตล์ไลน์ – 1ใหญ่+2+2 (5 ภาพ)",
        "1+2+2+1 – ใหญ่ทั้งบนล่าง (6 ภาพ)",
        "2×3 Grid",
        "3×2 Grid",
        "ภาพใหญ่ + เล็กข้าง",
        "2 ใหญ่ + 4 เล็ก",
        "Mosaic",
        "แถบแนวนอน",
    ])
    gap = st.slider("ช่องว่างระหว่างภาพ (px)", 0, 40, 8, step=2)
    bg_color_hex = st.color_picker("สีพื้นหลัง", "#ffffff")
    out_width = st.selectbox("ความกว้างเอาต์พุต", [1080, 1200, 1800, 2400], index=1)
    quality = st.slider("คุณภาพ JPEG", 70, 100, 92, step=1)

# --- Upload ---
uploaded = st.file_uploader(
    "อัปโหลดภาพ (สูงสุด 6 ภาพ)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
)

if not uploaded:
    st.info("👆 อัปโหลดภาพเพื่อเริ่มต้น")
    st.stop()

imgs = []
for f in uploaded[:6]:
    img = Image.open(f).convert("RGB")
    imgs.append(img)

n = len(imgs)
st.success(f"โหลดแล้ว {n} ภาพ")

# Show thumbnails
cols = st.columns(n)
for i, (col, img) in enumerate(zip(cols, imgs)):
    col.image(img, caption=f"ภาพ {i+1}", use_container_width=True)

# --- Helper ---
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def crop_fit(img, w, h):
    """Crop image to fill w×h (center crop)."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img2 = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img2.crop((left, top, left + w, top + h))

def make_canvas(W, H, bg):
    canvas = Image.new("RGB", (W, H), bg)
    return canvas

def place(canvas, img, x, y, w, h):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0:
        return
    piece = crop_fit(img, w, h)
    canvas.paste(piece, (x, y))

# --- Build layout ---
W = out_width
g = gap
bg = hex_to_rgb(bg_color_hex)

rects = []
H = W

if layout.startswith("สไตล์ไลน์"):
    H = int(W * 1.35)
    fw = W - g * 2
    r1h = int(H * 0.38)
    r2h = int((H - r1h - g * 4) / 2)
    hw = (fw - g) / 2
    rects = [
        (g, g, fw, r1h),
        (g, g*2+r1h, hw, r2h),
        (g*2+hw, g*2+r1h, hw, r2h),
        (g, g*3+r1h+r2h, hw, r2h),
        (g*2+hw, g*3+r1h+r2h, hw, r2h),
    ]

elif layout.startswith("1+2+2+1"):
    H = int(W * 1.6)
    fw = W - g * 2
    r1h = int(H * 0.28)
    midh = int((H - r1h * 2 - g * 5) / 2)
    hw = (fw - g) / 2
    rects = [
        (g, g, fw, r1h),
        (g, g*2+r1h, hw, midh),
        (g*2+hw, g*2+r1h, hw, midh),
        (g, g*3+r1h+midh, hw, midh),
        (g*2+hw, g*3+r1h+midh, hw, midh),
        (g, g*4+r1h+midh*2, fw, r1h),
    ]

elif layout.startswith("2×3"):
    H = int(W * 1.5)
    cols2, rows2 = 2, 3
    tw = (W - g * (cols2+1)) / cols2
    th = (H - g * (rows2+1)) / rows2
    for i in range(min(n, 6)):
        rects.append((g+(i%cols2)*(tw+g), g+(i//cols2)*(th+g), tw, th))

elif layout.startswith("3×2"):
    H = int(W * 0.7)
    cols2, rows2 = 3, 2
    tw = (W - g * (cols2+1)) / cols2
    th = (H - g * (rows2+1)) / rows2
    for i in range(min(n, 6)):
        rects.append((g+(i%cols2)*(tw+g), g+(i//cols2)*(th+g), tw, th))

elif layout.startswith("ภาพใหญ่"):
    H = int(W * 0.75)
    bw = W * 0.58 - g * 1.5
    sw = W * 0.42 - g * 1.5
    sh = (H - g * (n)) / max(n-1, 1)
    rects.append((g, g, bw, H - g*2))
    for i in range(1, n):
        rects.append((g*2+bw, g+(i-1)*(sh+g), sw, sh))

elif layout.startswith("2 ใหญ่"):
    H = W
    bh = H * 0.52 - g
    sh = H * 0.48 - g * 2
    bw = (W - g*3) / 2
    sw = (W - g*5) / 4
    rects.append((g, g, bw, bh))
    if n > 1: rects.append((g*2+bw, g, bw, bh))
    for i in range(2, n):
        rects.append((g+(i-2)*(sw+g), g*2+bh, sw, sh))

elif layout.startswith("Mosaic"):
    H = int(W * 0.75)
    hw2 = W * 0.55 - g * 1.5
    hh = (H - g*3) / 2
    sw2 = (W * 0.45 - g) / 2
    rects = [
        (g, g, hw2, hh),
        (hw2+g*2, g, sw2, hh),
        (hw2+g*2+sw2+g, g, sw2, hh),
        (g, g*2+hh, sw2, hh),
        (g+sw2+g, g*2+hh, sw2, hh),
        (g+sw2*2+g*2, g*2+hh, hw2, hh),
    ]

elif layout.startswith("แถบ"):
    H = int(W * n / 4)
    rh = (H - g*(n+1)) / n
    for i in range(n):
        rects.append((g, g+i*(rh+g), W-g*2, rh))

# --- Render ---
canvas = make_canvas(W, H, bg)
for i, r in enumerate(rects[:n]):
    place(canvas, imgs[i], *r)

# --- Preview ---
st.divider()
st.subheader("ตัวอย่างภาพ")
st.image(canvas, use_container_width=True)

# --- Download ---
buf = io.BytesIO()
canvas.save(buf, format="JPEG", quality=quality)
buf.seek(0)

st.download_button(
    label="⬇️ ดาวน์โหลดภาพ (JPG)",
    data=buf,
    file_name="photo-layout.jpg",
    mime="image/jpeg",
    use_container_width=True,
)

st.caption(f"ขนาด: {W}×{H}px · {n} ภาพ · Layout: {layout}")
