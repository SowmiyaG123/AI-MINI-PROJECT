import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def create_vector_db():
    # 1. Load your cleaned data
    df = pd.read_csv("Cleaned_Recipe_Dataset.csv")
    
    # 2. Prepare the documents for LangChain
    # We combine Title and Search_Ingredients for the "searchable" part
    documents = []
    for _, row in df.iterrows():
        content = f"Recipe: {row['Title']}\nIngredients: {row['Search_Ingredients']}"
        metadata = {
            "title": row['Title'],
            "full_ingredients": row['Ingredients'],
            "instructions": row['Instructions'],
            "image": row['Image_Name']
        }
        documents.append(Document(page_content=content, metadata=metadata))

    # 3. Create Embeddings (The "Brain" that understands meaning)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. Create and Save Vector Store (FAISS)
    print("Building vector database... this may take a minute.")
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local("faiss_recipe_index")
    print("Vector database saved successfully!")

if __name__ == "__main__":
    create_vector_db()