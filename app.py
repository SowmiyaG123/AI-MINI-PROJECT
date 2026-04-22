import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import re

st.set_page_config(page_title="PantryPilot: Exact Match", page_icon="🎯", layout="wide")

# Custom CSS for the three categories
st.markdown("""
    <style>
    .exact-card { border-left: 5px solid #16a34a; background-color: #f0fdf4; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .near-card { border-left: 5px solid #f59e0b; background-color: #fffbeb; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .status-tag { font-weight: bold; text-transform: uppercase; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

def clean_text(text):
    """Standardizes ingredient names for comparison."""
    # Remove measurements, punctuation, and common adjectives
    stop_words = {'large', 'small', 'medium', 'chopped', 'sliced', 'peeled', 'fresh', 'ground', 'teaspoon', 'tablespoon', 'cup', 'ounce', 'tbsp', 'tsp', 'lb', 'gram', 'kosher', 'unsalted'}
    text = re.sub(r'\(.*?\)|[\d\u00BC-\u00BE\u2150-\u215E/]+', '', text.lower())
    words = re.findall(r'\w+', text)
    return {w for w in words if w not in stop_words and len(w) > 2}

def classify_recipe(user_ingredients, doc):
    user_set = set()
    for item in user_ingredients.split(','):
        user_set.update(clean_text(item))
    
    raw_ingredients = re.findall(r"'(.*?)'", doc.metadata['full_ingredients'].lower())
    if not raw_ingredients: raw_ingredients = doc.metadata['full_ingredients'].lower().split(',')

    # Identify Required vs Optional (Heuristic: items with 'optional' in text are optional)
    required_items = []
    optional_items = []
    for line in raw_ingredients:
        if 'optional' in line:
            optional_items.append(clean_text(line))
        else:
            required_items.append(clean_text(line))

    # Check for missing required items
    missing_required = []
    for req in required_items:
        if not (req & user_set): # If intersection is empty, user is missing this
            missing_required.append(" ".join(req))

    # Check for missing optional items
    missing_optional = []
    for opt in optional_items:
        if not (opt & user_set):
            missing_optional.append(" ".join(opt))

    # Final Classification
    if not missing_required and not missing_optional:
        return "EXACT", []
    elif not missing_required and len(missing_optional) <= 2:
        return "NEAR", missing_optional
    else:
        return "EXCLUDE", missing_required

# --- 3. DATABASE LOAD ---
@st.cache_resource
def load_db():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.load_local("faiss_recipe_index", embeddings, allow_dangerous_deserialization=True)

# --- 4. MAIN APP ---
st.title("🎯 PantryPilot: Strict Match Engine")
user_input = st.text_input("Enter your available ingredients (comma separated):", placeholder="paneer, onion, salt, oil")

if user_input:
    db = load_db()
    # Search broadly (k=100) to find rare exact matches
    candidates = db.similarity_search(user_input, k=100)
    
    exact_list = []
    near_list = []

    for doc in candidates:
        status, missing = classify_recipe(user_input, doc)
        if status == "EXACT":
            exact_list.append(doc)
        elif status == "NEAR":
            near_list.append({"doc": doc, "missing": missing})

    # Display Results
    if not exact_list and not near_list:
        st.error("❌ No matches found. You are missing core ingredients for all known recipes.")
    
    if exact_list:
        st.subheader("✅ Perfect Matches (You have everything!)")
        for doc in exact_list[:5]:
            with st.container():
                st.markdown(f"""<div class='exact-card'>
                    <span class='status-tag' style='color: #16a34a;'>Exact Match</span>
                    <h4>{doc.metadata['title']}</h4>
                    <p><b>Instructions:</b> {doc.metadata['instructions'][:300]}...</p>
                </div>""", unsafe_allow_html=True)

    if near_list:
        st.subheader("⚠️ Near Matches (Missing 1-2 optional items)")
        for item in near_list[:5]:
            doc = item['doc']
            st.markdown(f"""<div class='near-card'>
                <span class='status-tag' style='color: #f59e0b;'>Near Match</span>
                <h4>{doc.metadata['title']}</h4>
                <p style='color: #92400e;'><b>Missing Optional:</b> {", ".join(item['missing'])}</p>
                <p><b>Instructions:</b> {doc.metadata['instructions'][:300]}...</p>
            </div>""", unsafe_allow_html=True)
else:
    st.info("Enter ingredients to see the strict matching in action.")