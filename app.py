import streamlit as st
import easyocr
import requests
import cv2
import numpy as np
from PIL import Image
import tempfile

# -------------------- Streamlit App Title --------------------
st.set_page_config(page_title="Food Product Analyzer", layout="centered")
st.title("🥫 Food Product Analyzer (OCR + OpenFoodFacts API)")
st.write("Upload a food product image. We'll extract its name using OCR and fetch nutritional information.")

# -------------------- Upload Section --------------------
uploaded_file = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="📷 Uploaded Image", use_column_width=True)

    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        image.save(tmp_file.name)
        temp_image_path = tmp_file.name

    # Convert to OpenCV format
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # OCR using EasyOCR
    with st.spinner("🔍 Extracting text using OCR..."):
        try:
            reader = easyocr.Reader(['en'], gpu=False)
            ocr_results = reader.readtext(temp_image_path)
        except Exception as e:
            st.error(f"❌ OCR failed: {e}")
            ocr_results = []

    extracted_texts = []
    if ocr_results:
        for bbox, text, _ in ocr_results:
            extracted_texts.append(text)
            top_left = tuple(map(int, bbox[0]))
            bottom_right = tuple(map(int, bbox[2]))
            cv2.rectangle(image_cv, top_left, bottom_right, (0, 255, 0), 2)
            cv2.putText(image_cv, text, (top_left[0], top_left[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        image_ocr = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        st.image(image_ocr, caption="🖼 OCR Result", use_column_width=True)

        combined_text = " ".join(extracted_texts)
    else:
        combined_text = ""

    # -------------------- Editable Product Name --------------------
    st.write("📝 **Review or Edit Product Name for Search**")
    user_input = st.text_input("Detected Product Name:", value=combined_text.strip())

    # -------------------- OpenFoodFacts API Call --------------------
    if user_input.strip():
        with st.spinner("📡 Searching OpenFoodFacts..."):
            api_url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={user_input}&search_simple=1&action=process&json=1"
            try:
                response = requests.get(api_url, timeout=10).json()
                products = response.get("products", [])

                if products:
                    product = products[0]
                    st.success("✅ Product found!")

                    st.subheader("🍽 Product Information")
                    st.write("**Product Name:**", product.get('product_name') or "N/A")
                    st.write("**Ingredients:**", product.get('ingredients_text') or "N/A")
                    st.write("**Calories (per 100g):**", product.get('nutriments', {}).get('energy-kcal_100g', "N/A"))
                else:
                    st.warning("⚠️ No matching product found in OpenFoodFacts. Try another name.")
            except Exception as e:
                st.error(f"❌ API request failed: {e}")
