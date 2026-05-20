import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import math
import json
from pathlib import Path

st.set_page_config(page_title="Brochure Maker", page_icon="📋", layout="wide")
st.title("📋 Brochure Maker")
st.caption("สร้างโบชัวร์สินค้าแบบ Makro รองรับ 1–20 รายการ จัดเรียงอัตโนมัติ")

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

def draw_text_wrapped(draw, text, x, y, max_w, font, color, line_gap=4):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    for l in lines:
        draw.text((x, y), l, font=font, fill=color)
        bbox = draw.textbbox((0, 0), l, font=font)
        y += (bbox[3] - bbox[1]) + line_gap
    return y

# ─── Font resolver ───────────────────────────────────────────────────────────
# ลำดับการหาฟอนต์:
# 1. Font Library (font_library/meta.json → font_library/xxx.ttf)
# 2. fonts/ folder ใน repo
# 3. root folder
# 4. default font

FONT_LIB_DIR = Path("font_library")
FONTS_DIR    = Path("fonts")

def _find_font_file(role="heading"):
    """หา path ฟอนต์จากหลาย source ตามลำดับ"""
    # 1. Font Library session state
    key  = "font_heading_key" if role == "heading" else "font_body_key"
    fkey = st.session_state.get(key)
    if fkey:
        fpath = FONT_LIB_DIR / f"{fkey}.ttf"
        if fpath.exists():
            return str(fpath)

    # 2. fonts/ folder — เลือกตาม role
    if FONTS_DIR.exists():
        if role == "heading":
            candidates = ["Prompt-Bold.ttf", "Mali-Bold.ttf",
                          "Prompt-SemiBold.ttf", "Mali-SemiBold.ttf"]
        else:
            candidates = ["Prompt-Regular.ttf", "Mali-Regular.ttf",
                          "Prompt-Light.ttf", "Mali-Light.ttf"]
        for c in candidates:
            fp = FONTS_DIR / c
            if fp.exists():
                return str(fp)
        # ถ้าไม่เจอที่ระบุ ใช้ไฟล์แรกที่เจอใน fonts/
        ttfs = list(FONTS_DIR.glob("*.ttf"))
        if ttfs:
            return str(ttfs[0])

    # 3. root folder
    for c in ["Prompt-Bold.ttf","Mali-Bold.ttf","Prompt-Regular.ttf","Mali-Regular.ttf"]:
        if Path(c).exists():
            return c

    return None

def fit_font(size):
    fpath = _find_font_file("heading")
    try:
        if fpath:
            return ImageFont.truetype(fpath, size)
    except:
        pass
    return ImageFont.load_default()

def fit_font_reg(size):
    fpath = _find_font_file("body")
    try:
        if fpath:
            return ImageFont.truetype(fpath, size)
    except:
        pass
    return ImageFont.load_default()

# ─── Sidebar ────────────────────────────────────────────────────────────────

THEMES = {
    "ทะเลลึก":   {"bg": "#0B3A5C", "header": "#0E4F80", "card": "#FFFFFF",
                  "accent": "#F0C040", "text_dark": "#1A1A2E", "text_light": "#FFFFFF",
                  "subtext": "#555577", "border": "#BED4E8"},
    "สดใส":      {"bg": "#E8F5E9", "header": "#2E7D32", "card": "#FFFFFF",
                  "accent": "#FF6F00", "text_dark": "#1B5E20", "text_light": "#FFFFFF",
                  "subtext": "#4E6147", "border": "#A5D6A7"},
    "พรีเมียม":  {"bg": "#1A1035", "header": "#2D1B69", "card": "#F5F3FF",
                  "accent": "#C084FC", "text_dark": "#2E1065", "text_light": "#FFFFFF",
                  "subtext": "#6D5A8A", "border": "#C4B5FD"},
    "ส้มสด":     {"bg": "#FFF3E0", "header": "#E65100", "card": "#FFFFFF",
                  "accent": "#1565C0", "text_dark": "#3E2723", "text_light": "#FFFFFF",
                  "subtext": "#6D4C41", "border": "#FFCC80"},
    "กราฟิกขาว": {"bg": "#F0F4FF", "header": "#1E3A8A", "card": "#FFFFFF",
                  "accent": "#DC2626", "text_dark": "#1E293B", "text_light": "#FFFFFF",
                  "subtext": "#475569", "border": "#BFDBFE"},
}

with st.sidebar:
    st.header("⚙️ ตั้งค่า")

    st.subheader("🏪 ข้อมูลร้าน")
    shop_name  = st.text_input("ชื่อร้าน", "Origin Seafood")
    slogan     = st.text_input("Slogan", "อาหารทะเลแช่แข็งคุณภาพสูง")
    promo_text = st.text_input("ป้ายโปรโมชั่น (ไม่บังคับ)", "สินค้าแนะนำประจำเดือน")
    contact    = st.text_input("ช่องทางติดต่อ", "LINE: @originseafood | Tel: 08X-XXX-XXXX")
    logo_file  = st.file_uploader("โลโก้ร้าน (ไม่บังคับ)", type=["png","jpg","jpeg","webp"])

    st.divider()
    st.subheader("🎨 ดีไซน์")
    theme_name = st.selectbox("ธีมสี", list(THEMES.keys()))

    # ── Font selector ────────────────────────────────────────────────────────
    _fmeta = {}
    _fmeta_file = FONT_LIB_DIR / "meta.json"
    if _fmeta_file.exists():
        with open(_fmeta_file, "r", encoding="utf-8") as _ff:
            _fmeta = json.load(_ff)

    # ตรวจสอบฟอนต์ที่มีอยู่
    _available_fonts = {}
    if _fmeta:
        for k, v in _fmeta.items():
            fp = FONT_LIB_DIR / f"{k}.ttf"
            if fp.exists():
                _available_fonts[v["label"]] = k
    # ดึงจาก fonts/ folder ด้วย
    if FONTS_DIR.exists():
        for fp in sorted(FONTS_DIR.glob("*.ttf")):
            label = fp.stem
            if label not in _available_fonts.values():
                _available_fonts[label] = f"__fonts__/{fp.name}"

    if _available_fonts:
        st.subheader("🔤 ฟอนต์")
        _fnames = list(_available_fonts.keys())

        _cur_h = st.session_state.get("font_heading_label", _fnames[0])
        _cur_b = st.session_state.get("font_body_label",    _fnames[0])
        if _cur_h not in _fnames: _cur_h = _fnames[0]
        if _cur_b not in _fnames: _cur_b = _fnames[0]

        _sel_h = st.selectbox("ฟอนต์หัวข้อ",  _fnames, index=_fnames.index(_cur_h), key="sb_font_h")
        _sel_b = st.selectbox("ฟอนต์เนื้อหา", _fnames, index=_fnames.index(_cur_b), key="sb_font_b")

        def _resolve_key(label):
            raw = _available_fonts[label]
            if raw.startswith("__fonts__/"):
                return None  # ใช้ path จาก fonts/ โดยตรง
            return raw

        st.session_state["font_heading_key"]   = _resolve_key(_sel_h)
        st.session_state["font_heading_label"] = _sel_h
        st.session_state["font_heading_file"]  = _available_fonts[_sel_h]
        st.session_state["font_body_key"]      = _resolve_key(_sel_b)
        st.session_state["font_body_label"]    = _sel_b
        st.session_state["font_body_file"]     = _available_fonts[_sel_b]
        st.caption(f"หัวข้อ: {_sel_h}  |  เนื้อหา: {_sel_b}")
    else:
        st.caption("💡 ไม่พบฟอนต์ — ตรวจสอบโฟลเดอร์ fonts/ ใน repo")

    # แสดงฟอนต์ที่ใช้จริง
    _hpath = _find_font_file("heading")
    _bpath = _find_font_file("body")
    if _hpath:
        st.caption(f"📂 หัวข้อ: `{_hpath}`")
    if _bpath:
        st.caption(f"📂 เนื้อหา: `{_bpath}`")

    bg_image_file = st.file_uploader("🖼️ ภาพพื้นหลัง (แทนที่สีธีม)", type=["png","jpg","jpeg","webp"])
    cols_count    = st.selectbox("จำนวนคอลัมน์", [3, 4, 5], index=1)
    out_w         = st.selectbox("ความกว้าง (px)", [2480, 2000, 1600, 1200], index=1,
                                 help="2480=A4 300dpi, 2000=โพสต์ออนไลน์")
    quality       = st.slider("คุณภาพ JPG", 70, 100, 90)
    out_format    = st.radio("รูปแบบ", ["JPG", "PNG"], horizontal=True)

    st.divider()
    # ── Badge Icons ──────────────────────────────────────────────────────────
    BADGE_DIR      = Path("badge_library")
    BADGE_META_FILE = BADGE_DIR / "meta.json"

    def load_badge_meta():
        if BADGE_META_FILE.exists():
            with open(BADGE_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    badge_meta  = load_badge_meta()
    col_options = {v["label"]: k for k, v in badge_meta.items()} if badge_meta else {}

    st.subheader("🔢 ไอคอนตัวเลข")
    badge_mode = st.radio("รูปแบบ badge",
        ["วงกลมสี (default)", "จาก Badge Library", "อัปโหลดใหม่"],
        horizontal=False)

    badge_imgs = {}

    if badge_mode == "จาก Badge Library":
        if not col_options:
            st.warning("ยังไม่มี Badge — ไปที่หน้า Badge Library ก่อนครับ")
        else:
            current_label = st.session_state.get("selected_badge_label", list(col_options.keys())[0])
            if current_label not in col_options:
                current_label = list(col_options.keys())[0]
            chosen_label = st.selectbox("เลือก Collection", list(col_options.keys()),
                                        index=list(col_options.keys()).index(current_label))
            col_key   = col_options[chosen_label]
            files_map = badge_meta[col_key].get("files", {})
            prev_nums = sorted(files_map.keys(), key=lambda x: int(x) if x.isdigit() else 999)[:6]
            pcols = st.columns(len(prev_nums)) if prev_nums else []
            for j, num in enumerate(prev_nums):
                fpath = BADGE_DIR / col_key / files_map[num]
                if fpath.exists():
                    with pcols[j]:
                        img = Image.open(fpath).convert("RGBA")
                        bg  = Image.new("RGBA", img.size, (180,180,180,255))
                        bg.paste(img, mask=img)
                        st.image(bg.convert("RGB"), caption=f"#{num}", width=52)
            st.caption(f"✅ {chosen_label} — {len(files_map)} badge")
            for num_str, fname in files_map.items():
                fpath = BADGE_DIR / col_key / fname
                if fpath.exists():
                    try:
                        badge_imgs[int(num_str)] = Image.open(fpath).convert("RGBA")
                    except:
                        pass

    elif badge_mode == "อัปโหลดใหม่":
        st.caption("ตั้งชื่อไฟล์เป็น 1.png, 2.png ...")
        badge_files = st.file_uploader("เลือกไฟล์ PNG",
            type=["png","webp"], accept_multiple_files=True, key="badge_upload")
        if badge_files:
            def _extract_num(f):
                try: return int(f.name.split(".")[0])
                except: return 999
            for i, bf in enumerate(sorted(badge_files, key=_extract_num)):
                try:
                    num = _extract_num(bf)
                    if num == 999: num = i + 1
                    badge_imgs[num] = Image.open(bf).convert("RGBA")
                except: pass
            if badge_imgs:
                pcols2 = st.columns(min(len(badge_imgs), 5))
                for j, (num, bimg) in enumerate(sorted(badge_imgs.items())[:5]):
                    with pcols2[j]:
                        bg = Image.new("RGBA", bimg.size, (180,180,180,255))
                        bg.paste(bimg, mask=bimg)
                        st.image(bg.convert("RGB"), caption=f"#{num}", width=52)

# ─── Product Entry ───────────────────────────────────────────────────────────

st.subheader("📦 รายการสินค้า")
st.caption("กรอกข้อมูลสินค้าและอัปโหลดภาพ")

if "num_products" not in st.session_state:
    st.session_state.num_products = 4

c1, c2 = st.columns([1, 4])
with c1:
    if st.button("➕ เพิ่มสินค้า"):
        st.session_state.num_products = min(st.session_state.num_products + 1, 30)
with c2:
    if st.button("➖ ลดสินค้า") and st.session_state.num_products > 1:
        st.session_state.num_products -= 1

n = st.session_state.num_products
products = []

for i in range(n):
    with st.expander(f"สินค้าที่ {i+1}", expanded=(i < 3)):
        col1, col2, col3 = st.columns([2, 1.5, 2])
        with col1:
            name   = st.text_input("ชื่อสินค้า",    key=f"name_{i}",   placeholder="เช่น หอยแมลงภู่แช่แข็ง")
            weight = st.text_input("น้ำหนัก/ขนาด",  key=f"weight_{i}", placeholder="เช่น 500g / 1kg")
        with col2:
            price  = st.text_input("ราคา (ไม่บังคับ)", key=f"price_{i}", placeholder="฿99")
        with col3:
            desc   = st.text_input("คำอธิบายสั้น",  key=f"desc_{i}",   placeholder="เช่น แพ็คสะอาด พร้อมปรุง")
        img_f = st.file_uploader("ภาพสินค้า", type=["jpg","jpeg","png","webp"],
                                  key=f"img_{i}", label_visibility="collapsed")
        products.append({"name": name, "weight": weight, "price": price,
                          "desc": desc, "img_file": img_f})

# ─── Generate ────────────────────────────────────────────────────────────────

if st.button("🖨️ สร้างโบชัวร์", type="primary", use_container_width=True):

    theme = THEMES[theme_name]
    T     = theme
    COLS  = cols_count
    W     = out_w
    PAD   = int(W * 0.025)
    GAP   = int(W * 0.012)

    card_w  = (W - PAD*2 - GAP*(COLS-1)) // COLS
    img_h   = int(card_w * 0.75)
    info_h  = int(card_w * 0.55)
    card_h  = img_h + info_h
    ROWS    = math.ceil(len(products) / COLS)

    header_h = int(W * 0.12)
    footer_h = int(W * 0.055)
    grid_h   = ROWS * card_h + (ROWS-1) * GAP
    H        = header_h + PAD + grid_h + PAD + footer_h

    if bg_image_file is not None:
        bg_raw = Image.open(bg_image_file).convert("RGB")
        canvas = crop_fit(bg_raw, W, H)
    else:
        canvas = Image.new("RGB", (W, H), hex_to_rgb(T["bg"]))

    draw = ImageDraw.Draw(canvas)

    # HEADER
    draw_rounded_rect(draw, 0, 0, W, header_h, 0, fill=hex_to_rgb(T["header"]))
    stripe_h = int(header_h * 0.06)
    draw.rectangle([0, header_h-stripe_h, W, header_h], fill=hex_to_rgb(T["accent"]))

    logo_area_w = 0
    if logo_file:
        try:
            logo = Image.open(logo_file).convert("RGBA")
            lh   = int(header_h * 0.7)
            lw   = int(logo.width * lh / logo.height)
            logo = logo.resize((lw, lh), Image.LANCZOS)
            canvas.paste(logo, (PAD, (header_h-lh)//2), logo)
            logo_area_w = lw + GAP
        except:
            pass

    text_x   = PAD + logo_area_w
    fn_big   = fit_font(int(header_h * 0.38))
    fn_small = fit_font_reg(int(header_h * 0.18))
    fn_promo = fit_font(int(header_h * 0.22))

    draw.text((text_x, int(header_h*0.12)), shop_name, font=fn_big,   fill=hex_to_rgb(T["text_light"]))
    draw.text((text_x, int(header_h*0.56)), slogan,    font=fn_small, fill=hex_to_rgb(T["accent"]))

    if promo_text:
        pb  = draw.textbbox((0,0), promo_text, font=fn_promo)
        pw  = pb[2]-pb[0]+GAP*2
        px  = W-PAD-pw
        py  = int(header_h*0.25)
        draw_rounded_rect(draw, px, py, pw, int(header_h*0.45), 12, fill=hex_to_rgb(T["accent"]))
        draw.text((px+GAP, py+int(header_h*0.1)), promo_text, font=fn_promo, fill=hex_to_rgb(T["text_dark"]))

    # GRID
    fn_name   = fit_font(int(card_w * 0.085))
    fn_weight = fit_font_reg(int(card_w * 0.07))
    fn_desc   = fit_font_reg(int(card_w * 0.065))
    fn_price  = fit_font(int(card_w * 0.1))
    fn_num    = fit_font(int(card_w * 0.09))

    badge_size    = int(card_w * 0.22)
    scaled_badges = {num: bimg.resize((badge_size, badge_size), Image.LANCZOS)
                     for num, bimg in badge_imgs.items()}

    for idx, prod in enumerate(products):
        col = idx % COLS
        row = idx // COLS
        cx  = PAD + col*(card_w+GAP)
        cy  = header_h + PAD + row*(card_h+GAP)

        draw_rounded_rect(draw, cx, cy, card_w, card_h, 12,
                          fill=hex_to_rgb(T["card"]),
                          outline=hex_to_rgb(T["border"]), outline_w=3)

        if prod["img_file"]:
            try:
                pimg  = Image.open(prod["img_file"]).convert("RGB")
                pimg  = crop_fit(pimg, card_w-4, img_h-4)
                mask  = Image.new("L", (card_w-4, img_h-4), 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.rounded_rectangle([0,0,card_w-5,img_h-5], radius=10, fill=255)
                canvas.paste(pimg, (cx+2, cy+2), mask)
            except:
                draw.rectangle([cx+2,cy+2,cx+card_w-2,cy+img_h-2], fill=hex_to_rgb(T["border"]))
        else:
            draw.rectangle([cx+2,cy+2,cx+card_w-2,cy+img_h-2], fill=hex_to_rgb(T["border"]))
            nb = draw.textbbox((0,0),"ไม่มีภาพ",font=fn_weight)
            nw = nb[2]-nb[0]
            draw.text((cx+(card_w-nw)//2, cy+img_h//2-10),"ไม่มีภาพ",font=fn_weight,fill=hex_to_rgb(T["subtext"]))

        # Badge
        badge_num = idx+1
        bx, by = cx+8, cy+8
        if badge_num in scaled_badges:
            bimg_s = scaled_badges[badge_num]
            canvas.paste(bimg_s, (bx, by), bimg_s)
        else:
            nb_r  = int(card_w*0.1)
            draw.ellipse([bx,by,bx+nb_r*2,by+nb_r*2], fill=hex_to_rgb(T["accent"]))
            num_s = str(badge_num)
            nb2   = draw.textbbox((0,0), num_s, font=fn_num)
            draw.text((bx+nb_r-(nb2[2]-nb2[0])//2, by+nb_r-(nb2[3]-nb2[1])//2),
                      num_s, font=fn_num, fill=hex_to_rgb(T["text_dark"]))

        iy    = cy+img_h+int(card_w*0.04)
        inner = card_w-GAP*2

        if prod["name"]:
            iy = draw_text_wrapped(draw, prod["name"], cx+GAP, iy, inner, fn_name, hex_to_rgb(T["text_dark"]), 6)
        if prod["weight"]:
            draw.text((cx+GAP, iy), prod["weight"], font=fn_weight, fill=hex_to_rgb(T["subtext"]))
            wb  = draw.textbbox((0,0), prod["weight"], font=fn_weight)
            iy += (wb[3]-wb[1])+4
        if prod["desc"]:
            iy = draw_text_wrapped(draw, prod["desc"], cx+GAP, iy, inner, fn_desc, hex_to_rgb(T["subtext"]), 4)
        if prod["price"]:
            pb2 = draw.textbbox((0,0), prod["price"], font=fn_price)
            px2 = cx+card_w-(pb2[2]-pb2[0])-GAP
            py2 = cy+card_h-(pb2[3]-pb2[1])-int(card_w*0.06)
            draw_rounded_rect(draw, px2-8, py2-6, (pb2[2]-pb2[0])+16, (pb2[3]-pb2[1])+12, 8, fill=hex_to_rgb(T["accent"]))
            draw.text((px2, py2), prod["price"], font=fn_price, fill=hex_to_rgb(T["text_dark"]))

    # FOOTER
    fy = H-footer_h
    draw.rectangle([0, fy, W, H], fill=hex_to_rgb(T["header"]))
    draw.rectangle([0, fy, W, fy+stripe_h], fill=hex_to_rgb(T["accent"]))
    fn_ft = fit_font_reg(int(footer_h*0.38))
    fb    = draw.textbbox((0,0), contact, font=fn_ft)
    fw2   = fb[2]-fb[0]
    draw.text(((W-fw2)//2, fy+int(footer_h*0.42)), contact, font=fn_ft, fill=hex_to_rgb(T["text_light"]))

    # Preview & Download
    st.divider()
    st.subheader("🖼️ ตัวอย่างโบชัวร์")
    preview = canvas.copy()
    max_pw  = 900
    if preview.width > max_pw:
        ratio   = max_pw/preview.width
        preview = preview.resize((max_pw, int(preview.height*ratio)), Image.LANCZOS)
    st.image(preview, use_container_width=True)

    buf = io.BytesIO()
    if out_format == "PNG":
        canvas.save(buf, format="PNG")
        buf.seek(0)
        st.download_button("⬇️ ดาวน์โหลด PNG", data=buf, file_name="brochure.png",
                           mime="image/png", use_container_width=True)
    else:
        canvas.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        st.download_button("⬇️ ดาวน์โหลด JPG", data=buf, file_name="brochure.jpg",
                           mime="image/jpeg", use_container_width=True)

    st.caption(f"ขนาด: {W}×{H}px · {len(products)} รายการ · {COLS} คอลัมน์ · {theme_name}")
