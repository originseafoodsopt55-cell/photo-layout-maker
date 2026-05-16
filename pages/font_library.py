import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import json
from pathlib import Path

st.set_page_config(page_title="Font Library", page_icon="🔤", layout="wide")
st.title("🔤 Font Library")
st.caption("คลังฟอนต์ — อัปโหลดครั้งเดียว เลือกใช้ได้ทุกหน้า")

# ─── Storage ─────────────────────────────────────────────────────────────────
FONT_DIR  = Path("font_library")
FONT_DIR.mkdir(exist_ok=True)
META_FILE = FONT_DIR / "meta.json"

def load_meta():
    if META_FILE.exists():
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_meta(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def get_font_path(font_key):
    return FONT_DIR / f"{font_key}.ttf"

def preview_font(font_path, size=36):
    """สร้างภาพ preview ข้อความภาษาไทย+อังกฤษ"""
    try:
        font = ImageFont.truetype(str(font_path), size)
        texts = ["อาหารทะเลแช่แข็ง", "Origin Seafood 123"]
        W, H = 500, 90
        img  = Image.new("RGB", (W, H), (30, 30, 40))
        draw = ImageDraw.Draw(img)
        y = 8
        for t in texts:
            draw.text((12, y), t, font=font, fill=(255, 255, 255))
            bb = draw.textbbox((0,0), t, font=font)
            y += (bb[3]-bb[1]) + 6
        return img
    except Exception as e:
        img  = Image.new("RGB", (500, 60), (60, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.text((10, 20), f"โหลดฟอนต์ไม่ได้: {e}", fill=(255, 100, 100))
        return img

meta = load_meta()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📚 คลังฟอนต์", "➕ อัปโหลดฟอนต์ใหม่", "🗑️ จัดการ"])

# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("เลือกฟอนต์เพื่อใช้งาน")

    if not meta:
        st.info("ยังไม่มีฟอนต์ในคลัง — ไปที่แท็บ 'อัปโหลดฟอนต์ใหม่' เพื่อเพิ่มครับ")
    else:
        # แสดงฟอนต์ที่ใช้งานอยู่
        cur_heading = st.session_state.get("font_heading_label", "—")
        cur_body    = st.session_state.get("font_body_label",    "—")
        st.info(f"✅ ใช้งานอยู่ → **หัวข้อ:** {cur_heading}  |  **เนื้อหา:** {cur_body}")
        st.divider()

        # แสดงฟอนต์ทั้งหมด
        for fkey, fdata in meta.items():
            label   = fdata.get("label", fkey)
            fpath   = get_font_path(fkey)
            col1, col2, col3, col4 = st.columns([2, 4, 1, 1])

            with col1:
                st.markdown(f"**{label}**")
                st.caption(f"`{fdata.get('filename','')}`")

            with col2:
                if fpath.exists():
                    prev = preview_font(fpath, size=30)
                    st.image(prev, use_container_width=True)
                else:
                    st.warning("ไม่พบไฟล์")

            with col3:
                if st.button("📝 ใช้เป็นหัวข้อ", key=f"h_{fkey}", use_container_width=True):
                    st.session_state["font_heading_key"]   = fkey
                    st.session_state["font_heading_label"] = label
                    st.success(f"ตั้ง '{label}' เป็นฟอนต์หัวข้อแล้ว!")
                    st.rerun()

            with col4:
                if st.button("📄 ใช้เป็นเนื้อหา", key=f"b_{fkey}", use_container_width=True):
                    st.session_state["font_body_key"]   = fkey
                    st.session_state["font_body_label"] = label
                    st.success(f"ตั้ง '{label}' เป็นฟอนต์เนื้อหาแล้ว!")
                    st.rerun()

            st.divider()

        # ปุ่มเลือกคู่ฟอนต์ยอดนิยม
        st.subheader("🎨 คู่ฟอนต์แนะนำ")
        font_keys = list(meta.keys())
        if len(font_keys) >= 2:
            pair_cols = st.columns(min(len(font_keys)//2, 4))
            for i in range(0, min(len(font_keys)-1, 8), 2):
                with pair_cols[i//2]:
                    k1, k2 = font_keys[i], font_keys[i+1]
                    l1, l2 = meta[k1]["label"], meta[k2]["label"]
                    st.markdown(f"**{l1}** + {l2}")
                    if st.button(f"ใช้คู่นี้", key=f"pair_{i}", use_container_width=True):
                        st.session_state["font_heading_key"]   = k1
                        st.session_state["font_heading_label"] = l1
                        st.session_state["font_body_key"]      = k2
                        st.session_state["font_body_label"]    = l2
                        st.success(f"เลือกคู่ '{l1}' + '{l2}' แล้ว!")
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("อัปโหลดฟอนต์ใหม่")
    st.caption("รองรับ .ttf และ .otf — สามารถอัปโหลดหลายไฟล์พร้อมกัน")

    uploaded_fonts = st.file_uploader(
        "เลือกไฟล์ฟอนต์ (.ttf / .otf)",
        type=["ttf", "otf"],
        accept_multiple_files=True,
        key="font_upload"
    )

    if uploaded_fonts:
        st.markdown(f"**เลือกไว้ {len(uploaded_fonts)} ไฟล์ — Preview:**")

        for uf in uploaded_fonts:
            fname    = uf.name
            fkey_raw = fname.replace(".ttf","").replace(".otf","")
            # ลบอักขระพิเศษ
            fkey     = "".join(c if c.isalnum() or c in "_-" else "_" for c in fkey_raw)

            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown(f"**{fname}**")
                # custom label
                label = st.text_input("ชื่อแสดง", value=fkey_raw.replace("-"," ").replace("_"," "),
                                      key=f"lbl_{fkey}")
            with col_b:
                # preview ชั่วคราว
                try:
                    uf.seek(0)
                    tmp_font = ImageFont.truetype(io.BytesIO(uf.read()), 30)
                    tmp_img  = Image.new("RGB", (500, 80), (30, 30, 40))
                    tmp_draw = ImageDraw.Draw(tmp_img)
                    tmp_draw.text((10, 8),  "อาหารทะเลแช่แข็ง", font=tmp_font, fill=(255,255,255))
                    tmp_draw.text((10, 46), "Origin Seafood 123", font=tmp_font, fill=(200,200,200))
                    st.image(tmp_img, use_container_width=True)
                except Exception as e:
                    st.warning(f"preview ไม่ได้: {e}")
            st.divider()

        if st.button("💾 บันทึกทั้งหมดลงคลัง", type="primary"):
            saved = 0
            for uf in uploaded_fonts:
                fname    = uf.name
                fkey_raw = fname.replace(".ttf","").replace(".otf","")
                fkey     = "".join(c if c.isalnum() or c in "_-" else "_" for c in fkey_raw)
                label    = st.session_state.get(f"lbl_{fkey}", fkey_raw)
                fpath    = get_font_path(fkey)
                uf.seek(0)
                fpath.write_bytes(uf.read())
                meta[fkey] = {"label": label, "filename": fname}
                saved += 1

            save_meta(meta)
            st.success(f"✅ บันทึก {saved} ฟอนต์สำเร็จ!")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("จัดการฟอนต์ในคลัง")

    if not meta:
        st.info("ยังไม่มีฟอนต์ในคลัง")
    else:
        for fkey, fdata in list(meta.items()):
            label = fdata.get("label", fkey)
            c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
            with c1:
                new_label = st.text_input("ชื่อ", value=label, key=f"rename_{fkey}")
            with c2:
                fpath = get_font_path(fkey)
                if fpath.exists():
                    prev = preview_font(fpath, size=24)
                    st.image(prev, use_container_width=True)
            with c3:
                if st.button("💾 แก้ชื่อ", key=f"save_{fkey}", use_container_width=True):
                    meta[fkey]["label"] = new_label
                    save_meta(meta)
                    st.success("บันทึกแล้ว!")
                    st.rerun()
            with c4:
                if st.button("🗑️ ลบ", key=f"del_{fkey}", use_container_width=True):
                    fpath = get_font_path(fkey)
                    if fpath.exists():
                        fpath.unlink()
                    del meta[fkey]
                    save_meta(meta)
                    for sk in ["font_heading_key","font_body_key"]:
                        if st.session_state.get(sk) == fkey:
                            del st.session_state[sk]
                    st.rerun()
            st.divider()

    st.subheader("📊 สรุป")
    st.write(f"ฟอนต์ทั้งหมด: **{len(meta)}** ไฟล์")
    if "font_heading_label" in st.session_state:
        st.write(f"ฟอนต์หัวข้อ: **{st.session_state['font_heading_label']}**")
    if "font_body_label" in st.session_state:
        st.write(f"ฟอนต์เนื้อหา: **{st.session_state['font_body_label']}**")
