import streamlit as st
from PIL import Image
import io
import json
from pathlib import Path
import time

st.set_page_config(page_title="Product Library", page_icon="📦", layout="wide")
st.title("📦 Product Library (คลังสินค้า)")
st.caption("คลังเก็บข้อมูลสินค้าและรูปภาพ — เพิ่มข้อมูลไว้เพื่อดึงไปใช้งานในหน้า Brochure Maker ได้ทันทีโดยไม่ต้องพิมพ์ใหม่")

# ─── Storage path ────────────────────────────────────────────────────────────
PRODUCT_LIB_DIR = Path("product_library")
IMAGES_DIR = PRODUCT_LIB_DIR / "images"

PRODUCT_LIB_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)
META_FILE = PRODUCT_LIB_DIR / "meta.json"

def load_products():
    if META_FILE.exists():
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_products(products_dict):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(products_dict, f, ensure_ascii=False, indent=2)

# ─── Load products ───────────────────────────────────────────────────────────
products = load_products()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📚 รายการคลังสินค้า", "➕ เพิ่มสินค้าใหม่", "🗑️ ลบหรือจัดการสินค้า"])

# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("สินค้าทั้งหมดที่มีในคลัง")

    if not products:
        st.info("💡 ยังไม่มีสินค้าในคลัง — ไปที่แท็บ 'เพิ่มสินค้าใหม่' เพื่อเพิ่มสินค้าชิ้นแรกของคุณ")
    else:
        cols_count = 3
        prod_keys = sorted(products.keys())
        rows = [prod_keys[i:i+cols_count] for i in range(0, len(prod_keys), cols_count)]

        for row in rows:
            grid_cols = st.columns(cols_count)
            for idx, prod_id in enumerate(row):
                prod_data = products[prod_id]
                with grid_cols[idx]:
                    with st.container(border=True):
                        img_path = prod_data.get("image_path")
                        if img_path and Path(img_path).exists():
                            try:
                                img = Image.open(img_path).convert("RGB")
                                st.image(img, use_container_width=True)
                            except:
                                st.error("ไม่สามารถเปิดภาพได้")
                        else:
                            st.caption("🚫 ไม่มีภาพสินค้า")
                        
                        st.markdown(f"### **{prod_data['name']}**")
                        if prod_data.get("weight"):
                            st.markdown(f"**ขนาด:** {prod_data['weight']}")
                        if prod_data.get("price"):
                            st.markdown(f"**ราคา:** :orange[{prod_data['price']}]")
                        if prod_data.get("desc"):
                            st.caption(prod_data["desc"])

# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("เพิ่มสินค้าชิ้นใหม่เข้าคลัง")
    st.caption("กรอกรายละเอียดสินค้าและอัปโหลดภาพประกอบ ข้อมูลทั้งหมดจะถูกเก็บไว้ใช้ซ้ำได้ตลอดเวลา")

    with st.form("add_product_form", clear_on_submit=True):
        name = st.text_input("ชื่อสินค้า *", placeholder="เช่น หอยแมลงภู่นิวซีแลนด์แช่แข็ง")
        weight = st.text_input("ขนาด / น้ำหนัก", placeholder="เช่น 500 กรัม หรือ 1 กิโลกรัม")
        price = st.text_input("ราคา", placeholder="เช่น ฿150 หรือ 150.-")
        desc = st.text_area("คำอธิบายสั้นๆ (แสดงใต้ขนาดสินค้า)", placeholder="เช่น คัดสรรพิเศษจากธรรมชาติ สะอาด ปลอดภัย")
        uploaded_file = st.file_uploader("ภาพสินค้า (ถ้ามี)", type=["png", "jpg", "jpeg", "webp"])
        
        submitted = st.form_submit_button("💾 บันทึกเข้าคลังสินค้า", type="primary")

        if submitted:
            if not name.strip():
                st.error("กรุณากรอกชื่อสินค้า")
            else:
                prod_id = f"prod_{int(time.time() * 1000)}"
                img_relative_path = ""
                if uploaded_file is not None:
                    ext = uploaded_file.name.split(".")[-1].lower()
                    if ext not in ["png", "jpg", "jpeg", "webp"]:
                        ext = "png"
                    img_filename = f"{prod_id}.{ext}"
                    img_dest_path = IMAGES_DIR / img_filename
                    
                    try:
                        img = Image.open(uploaded_file).convert("RGB")
                        img.save(img_dest_path)
                        img_relative_path = str(img_dest_path)
                    except Exception as e:
                        st.error(f"ไม่สามารถบันทึกภาพสินค้าได้: {e}")

                products[prod_id] = {
                    "name": name.strip(),
                    "weight": weight.strip(),
                    "price": price.strip(),
                    "desc": desc.strip(),
                    "image_path": img_relative_path
                }
                
                save_products(products)
                st.success(f"✅ บันทึกสินค้า '{name}' เรียบร้อยแล้ว! สามารถเรียกใช้งานได้ทันทีในหน้า Brochure Maker")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("จัดการและลบสินค้าในคลัง")

    if not products:
        st.info("ยังไม่มีสินค้าให้จัดการ")
    else:
        for prod_id, prod_data in list(products.items()):
            c1, c2, c3 = st.columns([1.5, 3.5, 1])
            with c1:
                img_path = prod_data.get("image_path")
                if img_path and Path(img_path).exists():
                    try:
                        img = Image.open(img_path).convert("RGB")
                        st.image(img, width=80)
                    except:
                        pass
                else:
                    st.caption("🚫 ไม่มีภาพ")
            with c2:
                st.markdown(f"**{prod_data['name']}**")
                meta_desc = []
                if prod_data.get('weight'): meta_desc.append(f"ขนาด: {prod_data['weight']}")
                if prod_data.get('price'): meta_desc.append(f"ราคา: {prod_data['price']}")
                if meta_desc:
                    st.caption(" · ".join(meta_desc))
            with c3:
                if st.button("🗑️ ลบ", key=f"del_prod_{prod_id}", use_container_width=True):
                    if img_path and Path(img_path).exists():
                        try:
                            Path(img_path).unlink()
                        except:
                            pass
                    del products[prod_id]
                    save_products(products)
                    st.success(f"ลบสินค้าเรียบร้อยแล้ว")
                    st.rerun()
            st.divider()
