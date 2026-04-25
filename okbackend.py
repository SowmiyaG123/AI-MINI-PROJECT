import pandas as pd
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import easyocr
import uvicorn
import os
import ast
from dotenv import load_dotenv

# ✅ FIXED IMPORTS (stable version)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Recipe Assistant Pro")

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development (later restrict)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =========================
# ROOT ROUTE ✅
# =========================
@app.get("/")
def home():
    return {"message": "Recipe Assistant API is running 🚀"}

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("ai-miniproj-dataset.csv")

print("CSV Columns:", df.columns)

df.columns = df.columns.str.strip().str.lower()
df.fillna("", inplace=True)

# =========================
# COLUMN MAPPING
# =========================
def get_col(name_options):
    for col in name_options:
        if col in df.columns:
            return col
    return None

recipe_col = get_col(["recipename", "recipe_name", "name"])
ingredients_col = get_col(["ingredients"])
instructions_col = get_col(["instructions", "steps", "directions"])

veg_col = get_col(["veg", "vegetarian"])
difficulty_col = get_col(["difficulty"])

# ✅ FIXED TIME
time_col = get_col(["minutes", "time", "cookingtime"])

nutrients_col = get_col(["nutrients", "nutrition"])

if not recipe_col or not ingredients_col or not instructions_col:
    raise Exception("Dataset missing required columns!")

# =========================
# SAFE LIST CONVERSION ✅
# =========================
def safe_list(value):
    try:
        return ast.literal_eval(value) if isinstance(value, str) else value
    except:
        return value

# =========================
# COMBINED TEXT
# =========================
df["combined"] = df.apply(
    lambda x: f"{x[recipe_col]} {x[ingredients_col]} {x[instructions_col]}",
    axis=1
)

# =========================
# EMBEDDINGS
# =========================
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

texts = df["combined"].tolist()
metadatas = df.to_dict(orient="records")

if os.path.exists("./db"):
    print("✅ Loading existing vector DB...")
    vector_db = Chroma(
        persist_directory="./db",
        embedding_function=embedding_model
    )
else:
    print("🚀 Creating new vector DB...")
    vector_db = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        persist_directory="./db"
    )
    vector_db.persist()

# =========================
# OCR
# =========================
reader = easyocr.Reader(['en'])

# =========================
# REQUEST MODEL
# =========================
class Query(BaseModel):
    query: str
    veg: str = None
    max_time: int = None
    difficulty: str = None

# =========================
# SEARCH FUNCTION
# =========================
def search_recipes(query, filters=None):
    results = vector_db.similarity_search_with_score(query, k=5)

    output = []

    for doc, score in results:
        data = doc.metadata

        similarity = round((1 - score) * 100, 2)

        if filters:
            if filters.get("veg") and veg_col:
                if filters["veg"] != data.get(veg_col):
                    continue

            if filters.get("difficulty") and difficulty_col:
                if filters["difficulty"] != data.get(difficulty_col):
                    continue

        output.append({
            "recipe": data.get(recipe_col),
            "ingredients": safe_list(data.get(ingredients_col)),   # ✅ FIXED
            "steps": safe_list(data.get(instructions_col)),        # ✅ FIXED
            "similarity": similarity,
            "time": data.get(time_col) if time_col else None,
            "difficulty": data.get(difficulty_col) if difficulty_col else None,
            "veg": data.get(veg_col) if veg_col else None,
            "nutrients": safe_list(data.get(nutrients_col)) if nutrients_col else None
        })

    return sorted(output, key=lambda x: x["similarity"], reverse=True)

# =========================
# CHAT
# =========================
@app.post("/chat")
def chat(req: Query):
    filters = {
        "veg": req.veg,
        "difficulty": req.difficulty
    }

    recipes = search_recipes(req.query, filters)

    if not recipes:
        return {"response": "No matching recipes found."}

    return {"recipes": recipes}

# =========================
# OCR
# =========================
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()

    with open("temp.jpg", "wb") as f:
        f.write(contents)

    result = reader.readtext("temp.jpg", detail=0)
    extracted_text = " ".join(result)

    recipes = search_recipes(extracted_text)

    return {
        "extracted": extracted_text,
        "recipes": recipes
    }

# =========================
# SUBSTITUTE
# =========================
@app.post("/substitute")
def substitute(req: Query):
    query = f"alternative recipes for {req.query}"
    recipes = search_recipes(query)

    return {"recipes": recipes}

# =========================
# RUN
# =========================
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
