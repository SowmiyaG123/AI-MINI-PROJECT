import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from groq import Groq
import os
import re

# --- 1. CONFIG & GROQ SETUP ---
st.set_page_config(page_title="PantryPilot AI", page_icon="👨‍🍳", layout="wide")

# Replace with your key
GROQ_API_KEY = "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" 
client = Groq(api_key=GROQ_API_KEY)

# --- 2. SMART PANTRY MEMORY ---
if "pantry" not in st.session_state:
    st.session_state.pantry = set()

def update_pantry(text):
    # Noise words to ignore during extraction
    noise = {
        'have', 'and', 'with', 'also', 'aslo', 'only', 'provide', 'give', 'i',
        'modified', 'recipe', 'items', 'except', 'other', 'all', 'the', 'please', 
        'now', 'let', 'lets', 'proceed', 'want', 'using', 'can', 'from', 'best'
    }
    # Extract only valid food words
    words = re.findall(r'\b\w+\b', text.lower())
    for word in words:
        if word not in noise and len(word) > 2:
            st.session_state.pantry.add(word)
    return ", ".join(list(st.session_state.pantry))

# --- 3. BACKEND LOGIC ---
@st.cache_resource
def load_db():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.load_local("faiss_recipe_index", embeddings, allow_dangerous_deserialization=True)

def get_context(query):
    db = load_db()
    docs = db.similarity_search(query, k=5)
    context = ""
    for i, d in enumerate(docs):
        context += f"\n-- RECIPE {i+1} --\nName: {d.metadata['title']}\nIngredients: {d.metadata['ingredients']}\nInstructions: {d.metadata['instructions']}\n"
    return context

# --- 4. UI DESIGN ---
st.title("👨‍🍳 PantryPilot: Intelligent Chef")
st.sidebar.header("🛒 Your Kitchen Inventory")
st.sidebar.info(", ".join(list(st.session_state.pantry)) if st.session_state.pantry else "Waiting for ingredients...")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Tell me what you have in your kitchen, and I'll find a match."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. CHAT INTERACTION ---
if prompt := st.chat_input("I have paneer, peas, and onions..."):
    current_pantry = update_pantry(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Analyzing recipes against your pantry..."):
        try:
            recipe_context = get_context(current_pantry)
            
            system_prompt = f"""
            You are a Professional Chef. 
            USER FULL PANTRY: {current_pantry}
            
            RECIPES TO ANALYZE:
            {recipe_context}

            STRICT INSTRUCTIONS:
            1. Use the FULL PANTRY to validate matches.
            2. Mark as '✅ EXACT MATCH' only if ALL core ingredients (proteins, veggies, starch) are in the pantry.
            3. Mark as '⚠️ NEAR MATCH' if only minor spices/oils are missing.
            4. If the user asks for a 'modified' version, suggest how to cook the dish using ONLY their {current_pantry}.
            5. Always start your response by acknowledging their full pantry.
            """

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"My pantry has {current_pantry}. What is the best option?"}
                ],
                temperature=0.1
            )
            
            response = completion.choices[0].message.content
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun() # Updates the sidebar
            
        except Exception as e:
            st.error(f"Error: {e}")