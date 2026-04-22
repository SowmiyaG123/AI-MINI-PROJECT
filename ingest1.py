import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import os

# --- CONFIG ---
CSV_PATH = "Cleaned_Recipe_Dataset.csv"
INDEX_DIR = "faiss_recipe_index1"

def run_ingestion():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found!")
        return

    print("Reading CSV...")
    df = pd.read_csv(CSV_PATH)
    
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Map your columns specifically
    col_map = {
        "title": "title",
        "ingredients": "ingredients", 
        "instructions": "instructions"
    }

    # Verify columns
    for key, val in col_map.items():
        if val not in df.columns:
            print(f"❌ ERROR: Column '{val}' not found. Available: {df.columns.tolist()}")
            return

    df = df.fillna("")
    documents = []
    
    print("Processing recipes into vector format...")
    for _, row in df.iterrows():
        content = f"Recipe: {row[col_map['title']]}. Ingredients: {row[col_map['ingredients']]}"
        metadata = {
            "title": row[col_map['title']],
            "ingredients": row[col_map['ingredients']],
            "instructions": row[col_map['instructions']]
        }
        documents.append(Document(page_content=content, metadata=metadata))

    print("Generating Embeddings (HuggingFace)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("Saving FAISS Index...")
    vector_db = FAISS.from_documents(documents, embeddings)
    vector_db.save_local(INDEX_DIR)
    print("✅ Ingestion Complete!")

if __name__ == "__main__":
    run_ingestion()