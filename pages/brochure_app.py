import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import math
import textwrap

st.set_page_config(page_title="Luxury Brochure Maker", page_icon="📋", layout="wide")
st.title("📋 Luxury Brochure Maker")
st.caption("ระบบสร้างแคตตาล็อกสินค้าพรีเมียม - Smart Layout & Luxury Design")

# ─── Helpers ────────────────────────────────────────────────────────────────

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def crop_fit(img, w, h):
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img2 = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top  = (nh - h) // 2
    return img2.crop((left, top, left + w, top + h))

def draw_rounded_rect(draw, x, y, w, h, r, fill, outline=None, outline_w=2):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill,
                            outline=outline, width=outline_w)

def fit_font(size):
    # พยายามโหลด Prompt ก่อน ถ้าไม่มีไป Mali ถ้าไม่มีไปพื้นฐาน
    fonts = ["Prompt-Bold.ttf", "Mali-Bold.ttf"]
    for f in fonts:
        try:
            return ImageFont.truetype(f, size)
        except:
            continue
    return ImageFont.load_default()

def fit_font_reg(size):
    fonts = ["Prompt-Regular.ttf", "Mali-Regular.ttf"]
    for f in fonts:
        try:
            return ImageFont.truetype(f, size)
        except:
            continue
    return ImageFont.load_default()

def draw_text_wrapped(draw, text, x, y, max_w, font, color, line_gap=4):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            line = test
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    for l in lines:
        draw.text((x, y), l, font=font, fill=color)
        bbox = draw.textbbox((0,0), l, font=font)
        y += (bbox[3] - bbox[1]) + line_gap
    return y

# ─── Themes (Luxury Focused) ──────────────────────────────────────────────────

THEMES = {
    "Luxury Export": {"bg": "#F4F6F8", "header": "#081B33", "card": "#FFFFFF",
                      "accent": "#D4A94D", "text_dark": "#0F172A", "text_light": "#FFFFFF",
                      "subtext": "#64748B", "border": "#E2E8F0"},
    "Minimal Clean": {"bg": "#F8FAFC", "header": "#0F172A", "card": "#FFFFFF",
                      "accent": "#0EA5E9", "text_dark": "#111827", "text_light": "#FFFFFF",
                      "subtext": "#6B7280", "border": "#E5E7EB"},
    "Commercial":    {"bg": "#EEF2FF", "header": "#1E3A8A", "card": "#FFFFFF",
                      "accent": "#F59E0B", "text_dark": "#0F172A", "text_light": "#FFFFFF",
                      "subtext": "#475569", "border": "#CBD5E1"},
    "ทะเลลึก (Classic)": {"bg": "#0B3A5C", "header": "#0E4F80", "card": "#FFFFFF",
                      "accent": "#F0C040", "text_dark": "#1A1A2E", "text_light": "#FFFFFF",
                      "subtext": "#555577", "border": "#BED4E8"},
}

# ─── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ ตั้งค่า")

    st.subheader("🏪 ข้อมูลร้าน")
    shop_name   = st.text_input("ชื่อร้าน", "Origin Seafood")
    slogan      = st.text_input("Slogan", "Premium Frozen Seafood")
    promo_text  = st.text_input("ป้ายโปรโมชั่น", "Fresh Frozen Premium")
    contact     = st.text_input("ช่องทางติดต่อ", "LINE: @originseafood")
    logo_file   = st.file_uploader("โลโก้ร้าน", type=["png","jpg","jpeg","webp"])

    st.divider()
    st.subheader("🎨 ดีไซน์")
    theme_name  = st.selectbox("ธีม", list(THEMES.keys()))
    
    layout_mode = st.selectbox("🧠 Layout Mode", ["AUTO", "Portrait", "Landscape"], index=0)
    
    bg_image_file = st.file_uploader("🖼️ ภาพพื้นหลัง (ถ้ามี)", type=["png","jpg","jpeg","webp"])

    cols_count  = st.selectbox("จำนวนคอลัมน์ (ถ้าไม่ใช่ AUTO)", [3, 4, 5], index=1)
    out_w_manual = st.selectbox("ขนาดความกว้าง (px)", [2480, 2000, 1600], index=1)
    quality     = st.slider("คุณภาพ JPG", 70, 100, 92)
    out_format  = st.radio("รูปแบบไฟล์", ["JPG","PNG"], horizontal=True)

# ─── Product Input ──────────────────────────────────────────────────────────

st.subheader("📦 รายการสินค้า")
if "num_products" not in st.session_state: st.session_state.num_products = 4

c1, c2 = st.columns([1,4])
with c1:
    if st.button("➕ เพิ่ม"): st.session_state.num_products = min(st.session_state.num_products + 1, 30)
with c2:
    if st.button("➖ ลด") and st.session_state.num_products > 1: st.session_state.num_products -= 1

products = []
for i in range(st.session_state.num_products):
    with st.expander(f"สินค้าที่ {i+1}", expanded=(i < 3)):
        col1, col2, col3 = st.columns([2, 1.5, 2])
        with col1:
            name = st.text_input("ชื่อสินค้า", key=f"name_{i}")
            weight = st.text_input("น้ำหนัก", key=f"weight_{i}")
        with col2:
            price = st.text_input("ราคา", key=f"price_{i}")
        with col3:
            desc = st.text_input("รายละเอียด", key=f"desc_{i}")
        img_f = st.file_uploader("ภาพสินค้า", type=["jpg","jpeg","png","webp"], key=f"img_{i}")
        products.append({"name": name, "weight": weight, "price": price, "desc": desc, "img_file": img_f})

# ─── Generate ───────────────────────────────────────────────────────────────

if st.button("🖨️ สร้างโบชัวร์พรีเมียม", type="primary", use_container_width=True):
    T = THEMES[theme_name]
    count = len(products)

    # --- SMART LAYOUT LOGIC ---
    if layout_mode == "AUTO":
        if count <= 4: COLS, W = 2, 1600
        elif count <= 8: COLS, W = 3, 1800
        elif count <= 12: COLS, W = 4, 2000
        else: COLS, W = 5, 2200
    else:
        W = out_w_manual
        COLS = 4 if layout_mode == "Portrait" else 5 if layout_mode == "Landscape" else cols_count

    PAD = int(W * 0.03)
    GAP = int(W * 0.014)
    
    # --- CARD SIZING ---
    card_w = (W - PAD*2 - GAP*(COLS-1)) // COLS
    img_h  = int(card_w * 0.68)
    info_h = int(card_w * 0.45)
    card_h = img_h + info_h
    ROWS   = math.ceil(count / COLS)

    header_h = int(W * 0.08)
    footer_h = int(W * 0.045)
    grid_h   = ROWS * card_h + (ROWS-1) * GAP
    H        = header_h + PAD + grid_h + PAD + footer_h

    # --- CANVAS ---
    if bg_image_file:
        canvas = crop_fit(Image.open(bg_image_file).convert("RGB"), W, H)
    else:
        canvas = Image.new("RGB", (W, H), hex_to_rgb(T["bg"]))
    
    draw = ImageDraw.Draw(canvas)

    # --- HEADER ---
    draw.rectangle([0, 0, W, header_h], fill=hex_to_rgb(T["header"]))
    stripe_h = int(header_h * 0.05)
    draw.rectangle([0, header_h-stripe_h, W, header_h], fill=hex_to_rgb(T["accent"]))

    logo_w = 0
    if logo_file:
        try:
            logo = Image.open(logo_file).convert("RGBA")
            lh = int(header_h * 0.6); lw = int(logo.width * lh / logo.height)
            logo = logo.resize((lw, lh), Image.LANCZOS)
            canvas.paste(logo, (PAD, (header_h-lh)//2), logo)
            logo_w = lw + GAP
        except: pass

    fn_big = fit_font(int(header_h * 0.3)); fn_small = fit_font_reg(int(header_h * 0.16)); fn_promo = fit_font(int(header_h * 0.18))
    draw.text((PAD+logo_w, int(header_h*0.18)), shop_name, font=fn_big, fill=hex_to_rgb(T["text_light"]))
    draw.text((PAD+logo_w, int(header_h*0.55)), slogan, font=fn_small, fill=hex_to_rgb(T["accent"]))

    if promo_text:
        pb = draw.textbbox((0,0), promo_text, font=fn_promo); pw = pb[2]-pb[0]+GAP*2
        draw_rounded_rect(draw, W-PAD-pw, int(header_h*0.3), pw, int(header_h*0.35), 15, fill=hex_to_rgb(T["accent"]))
        draw.text((W-PAD-pw+GAP, int(header_h*0.37)), promo_text, font=fn_promo, fill=hex_to_rgb(T["text_dark"]))

    # --- GRID ---
    fn_name = fit_font(int(card_w * 0.08)); fn_weight = fit_font_reg(int(card_w * 0.06)); fn_desc = fit_font_reg(int(card_w * 0.055)); fn_price = fit_font(int(card_w * 0.09)); fn_num = fit_font(int(card_w * 0.07))

    for idx, prod in enumerate(products):
        cx = PAD + (idx%COLS)*(card_w+GAP); cy = header_h + PAD + (idx//COLS)*(card_h+GAP)

        # Soft Shadow (Solid Gray fallback for RGB)
        shd = int(card_w * 0.015)
        draw.rounded_rectangle([cx+shd, cy+shd, cx+card_w+shd, cy+card_h+shd], radius=24, fill=(210,215,220))
        
        # Card
        draw_rounded_rect(draw, cx, cy, card_w, card_h, 24, fill=hex_to_rgb(T["card"]), outline=hex_to_rgb(T["border"]), outline_w=2)

        # Product Image
        if prod["img_file"]:
            try:
                pimg = crop_fit(Image.open(prod["img_file"]).convert("RGB"), card_w-4, img_h-4)
                mask = Image.new("L", (card_w-4, img_h-4), 0); mdraw = ImageDraw.Draw(mask)
                mdraw.rounded_rectangle([0,0,card_w-5,img_h-5], radius=20, fill=255)
                canvas.paste(pimg, (cx+2, cy+2), mask)
            except: draw.rectangle([cx+2, cy+2, cx+card_w-2, cy+img_h-2], fill=hex_to_rgb(T["border"]))
        else:
             draw.rectangle([cx+2, cy+2, cx+card_w-2, cy+img_h-2], fill=hex_to_rgb(T["border"]))

        # Number Badge
        nb_r = int(card_w * 0.07)
        draw.ellipse([cx+12, cy+12, cx+12+nb_r*2, cy+12+nb_r*2], fill=hex_to_rgb(T["accent"]))
        draw.text((cx+12+nb_r-8, cy+12+nb_r-12), str(idx+1), font=fn_num, fill=hex_to_rgb(T["text_dark"]))

        # Info
        iy = cy + img_h + int(card_w*0.05)
        if prod["name"]: iy = draw_text_wrapped(draw, prod["name"], cx+GAP, iy, card_w-GAP*2, fn_name, hex_to_rgb(T["text_dark"]))
        if prod["weight"]: 
            draw.text((cx+GAP, iy), prod["weight"], font=fn_weight, fill=hex_to_rgb(T["subtext"]))
            iy += int(card_w*0.08)
        if prod["desc"]: draw_text_wrapped(draw, prod["desc"], cx+GAP, iy, card_w-GAP*2, fn_desc, hex_to_rgb(T["subtext"]))

        if prod["price"]:
            pb2 = draw.textbbox((0,0), prod["price"], font=fn_price); pw2 = pb2[2]-pb2[0]
            # ปรับสีป้ายราคาให้ตาม Header Theme (Luxury)
            draw_rounded_rect(draw, cx+card_w-pw2-35, cy+card_h-int(card_w*0.15), pw2+25, int(card_w*0.12), 15, fill=hex_to_rgb(T["header"]))
            draw.text((cx+card_w-pw2-22, cy+card_h-int(card_w*0.13)), prod["price"], font=fn_price, fill="#FFFFFF")

    # --- FOOTER ---
    fy = H - footer_h
    draw.rectangle([0, fy, W, H], fill=hex_to_rgb(T["header"]))
    fn_ft = fit_font_reg(int(footer_h*0.35)); ft_b = draw.textbbox((0,0), contact, font=fn_ft)
    draw.text(((W-(ft_b[2]-ft_b[0]))//2, fy+int(footer_h*0.3)), contact, font=fn_ft, fill="#FFFFFF")

    st.divider()
    st.subheader("🖼️ ตัวอย่างโบชัวร์")
    preview = canvas.copy()
    if preview.width > 900: preview = preview.resize((900, int(preview.height*(900/preview.width))), Image.LANCZOS)
    st.image(preview, use_container_width=True)

    buf = io.BytesIO()
    if out_format == "PNG":
        canvas.save(buf, format="PNG"); buf.seek(0)
        st.download_button("⬇️ ดาวน์โหลด PNG", data=buf, file_name="luxury_brochure.png", mime="image/png", use_container_width=True)
    else:
        canvas.save(buf, format="JPEG", quality=quality); buf.seek(0)
        st.download_button("⬇️ ดาวน์โหลด JPG", data=buf, file_name="luxury_brochure.jpg", mime="image/jpeg", use_container_width=True)
