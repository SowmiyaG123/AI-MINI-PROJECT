import streamlit as st
from backend import RecipeRAG

st.set_page_config(page_title="AI Recipe Assistant", layout="wide")

st.title("🍳 AI Cooking Assistant")
st.markdown("Smart recipe suggestions using AI + RAG")

# ---------------- SIDEBAR ----------------
st.sidebar.header("🔍 Filters")

recipe_type = st.sidebar.selectbox(
    "Recipe Type",
    ["Any", "Vegetarian", "Non-Vegetarian"]
)

time_limit = st.sidebar.selectbox(
    "Max Cooking Time",
    ["Any", "15 mins", "30 mins", "60 mins"]
)

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load_model():
    return RecipeRAG("Cleaned_Recipe_Dataset.csv")

model = load_model()

# ---------------- CHAT ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- INPUT ----------------
user_input = st.chat_input("Enter ingredients (e.g., onion, tomato, rice)")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("🍳 Cooking ideas coming up..."):
            response = model.run(user_input, recipe_type, time_limit)

            # Clean UI display
            st.markdown("### 🍽️ Recommended Recipes")
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
