import streamlit as st
from PIL import Image
import io
import os
import base64
import json
from pathlib import Path

st.set_page_config(page_title="Badge Library", page_icon="🔢", layout="wide")
st.title("🔢 Badge Library")
st.caption("คลังไอคอนตัวเลข PNG พื้นหลังใส — อัปโหลดครั้งเดียว ใช้ได้ทุกครั้ง")

# ─── Storage path ────────────────────────────────────────────────────────────
BADGE_DIR = Path("badge_library")
BADGE_DIR.mkdir(exist_ok=True)
META_FILE = BADGE_DIR / "meta.json"

def load_meta():
    if META_FILE.exists():
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_meta(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def get_badge_path(collection, filename):
    col_dir = BADGE_DIR / collection
    col_dir.mkdir(exist_ok=True)
    return col_dir / filename

def img_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ─── Load meta ───────────────────────────────────────────────────────────────
meta = load_meta()  # { "collection_name": { "label": "...", "files": {"1": "1.png", ...} } }

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📚 คลัง Badge", "➕ อัปโหลด Collection ใหม่", "🗑️ จัดการ"])

# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("เลือก Collection เพื่อใช้งาน")

    if not meta:
        st.info("ยังไม่มี Collection — ไปที่แท็บ 'อัปโหลด Collection ใหม่' เพื่อเพิ่มครับ")
    else:
        for col_key, col_data in meta.items():
            label     = col_data.get("label", col_key)
            files_map = col_data.get("files", {})  # {"1": "1.png", "2": "2.png", ...}

            with st.expander(f"🗂️ {label}  ({len(files_map)} badge)", expanded=True):
                # Preview grid
                nums_sorted = sorted(files_map.keys(), key=lambda x: int(x) if x.isdigit() else 999)
                cols_per_row = 10
                rows = [nums_sorted[i:i+cols_per_row] for i in range(0, len(nums_sorted), cols_per_row)]

                for row in rows:
                    row_cols = st.columns(len(row))
                    for j, num in enumerate(row):
                        fpath = get_badge_path(col_key, files_map[num])
                        if fpath.exists():
                            with row_cols[j]:
                                img = Image.open(fpath).convert("RGBA")
                                # วาดบน checkerboard เพื่อแสดง transparency
                                bg  = Image.new("RGBA", img.size, (200, 200, 200, 255))
                                bg.paste(img, mask=img)
                                st.image(bg.convert("RGB"), caption=f"#{num}", width=60)

                # Action buttons
                bc1, bc2 = st.columns([1, 3])
                with bc1:
                    if st.button(f"✅ ใช้ Collection นี้", key=f"use_{col_key}"):
                        st.session_state["selected_badge_collection"] = col_key
                        st.session_state["selected_badge_label"]      = label
                        st.success(f"เลือก '{label}' แล้ว! กลับไปหน้า Brochure Maker ได้เลยครับ")

        # Show current selection
        if "selected_badge_collection" in st.session_state:
            sel = st.session_state["selected_badge_label"]
            st.success(f"✅ ใช้งานอยู่: **{sel}** — หน้า Brochure Maker จะโหลด badge ชุดนี้อัตโนมัติ")

# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("อัปโหลด Collection ใหม่")
    st.caption("1 Collection = ชุด badge ที่ใช้คู่กัน เช่น 'อีโมจิทะเล', 'วงกลมทอง', 'ตัวเลขน่ารัก'")

    col_label = st.text_input("ชื่อ Collection", placeholder="เช่น วงกลมทอง, อีโมจิตัวเลข")
    col_key_input = st.text_input("ID (ภาษาอังกฤษ ไม่มีเว้นวรรค)", placeholder="เช่น gold_circle, emoji_num")

    uploaded_badges = st.file_uploader(
        "อัปโหลด PNG พื้นหลังใส (ตั้งชื่อไฟล์เป็น 1.png, 2.png, ... หรือระบบจะเรียงตามลำดับ)",
        type=["png", "webp"],
        accept_multiple_files=True,
        key="new_badge_upload"
    )

    if uploaded_badges:
        st.markdown("**Preview ก่อนบันทึก:**")
        def extract_num(f):
            try:
                return int(f.name.split(".")[0])
            except:
                return 999

        sorted_files = sorted(uploaded_badges, key=extract_num)
        prev_cols = st.columns(min(len(sorted_files), 10))
        for j, bf in enumerate(sorted_files[:10]):
            with prev_cols[j]:
                img = Image.open(bf).convert("RGBA")
                bg  = Image.new("RGBA", img.size, (200, 200, 200, 255))
                bg.paste(img, mask=img)
                num = extract_num(bf) if extract_num(bf) != 999 else j+1
                st.image(bg.convert("RGB"), caption=f"#{num}", width=60)
            bf.seek(0)

    if st.button("💾 บันทึก Collection", type="primary", disabled=not (col_label and col_key_input and uploaded_badges)):
        def extract_num(f):
            try:
                return int(f.name.split(".")[0])
            except:
                return 999

        sorted_files = sorted(uploaded_badges, key=extract_num)
        files_map = {}
        for j, bf in enumerate(sorted_files):
            num = extract_num(bf) if extract_num(bf) != 999 else j + 1
            fname = f"{num}.png"
            fpath = get_badge_path(col_key_input, fname)
            bf.seek(0)
            img = Image.open(bf).convert("RGBA")
            img.save(fpath, format="PNG")
            files_map[str(num)] = fname

        meta[col_key_input] = {"label": col_label, "files": files_map}
        save_meta(meta)
        st.success(f"✅ บันทึก Collection '{col_label}' สำเร็จ! ({len(files_map)} badge)")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("จัดการ Collection")

    if not meta:
        st.info("ยังไม่มี Collection")
    else:
        for col_key, col_data in list(meta.items()):
            label = col_data.get("label", col_key)
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{label}** `{col_key}` — {len(col_data.get('files', {}))} badge")
            with c2:
                if st.button("✅ เลือกใช้", key=f"sel2_{col_key}"):
                    st.session_state["selected_badge_collection"] = col_key
                    st.session_state["selected_badge_label"]      = label
                    st.success(f"เลือก '{label}' แล้ว!")
            with c3:
                if st.button("🗑️ ลบ", key=f"del_{col_key}"):
                    # ลบไฟล์
                    col_dir = BADGE_DIR / col_key
                    if col_dir.exists():
                        for f in col_dir.iterdir():
                            f.unlink()
                        col_dir.rmdir()
                    del meta[col_key]
                    save_meta(meta)
                    if st.session_state.get("selected_badge_collection") == col_key:
                        del st.session_state["selected_badge_collection"]
                    st.rerun()

    st.divider()
    if "selected_badge_collection" in st.session_state:
        st.info(f"✅ ใช้งานอยู่: **{st.session_state.get('selected_badge_label', '')}**")
