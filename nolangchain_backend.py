import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class RecipeRAG:
    def __init__(self, data_path):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        self.df = pd.read_csv(data_path)
        self.df['Search_Ingredients'] = self.df['Search_Ingredients'].fillna("")
        self.df['Instructions'] = self.df['Instructions'].fillna("")

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.chroma = chromadb.Client()
        self.collection = self.chroma.get_or_create_collection("recipes")

        if self.collection.count() == 0:
            self._load_data()

    # ----------------------------
    # LOAD DATA INTO VECTOR DB
    # ----------------------------
    def _load_data(self):
        docs, embeddings, ids = [], [], []

        for i, row in self.df.iterrows():
            text = f"""
Title: {row['Title']}
Ingredients: {row['Ingredients']}
Instructions: {row['Instructions']}
Search_Ingredients: {row['Search_Ingredients']}
"""

            emb = self.model.encode(text).tolist()

            docs.append(text)
            embeddings.append(emb)
            ids.append(str(i))

        self.collection.add(documents=docs, embeddings=embeddings, ids=ids)

    # ----------------------------
    # PREPROCESS
    # ----------------------------
    def _preprocess(self, text):
        return [i.strip().lower() for i in text.split(",") if i.strip()]

    def _match_score(self, user, recipe):
        recipe_list = [i.strip().lower() for i in recipe.split(",") if i.strip()]
        if not recipe_list:
            return 0
        return round(sum(1 for i in user if i in recipe_list) / len(recipe_list), 2)

    def _missing(self, user, recipe):
        recipe_list = [i.strip().lower() for i in recipe.split(",") if i.strip()]
        return [i for i in recipe_list if i not in user]

    def _is_veg(self, ingredients):
        nonveg = ["chicken", "mutton", "egg", "fish", "beef", "prawn"]
        return not any(nv in ingredients.lower() for nv in nonveg)

    def _time_estimate(self, instructions):
        length = len(instructions.split())
        if length < 80:
            return 15
        elif length < 150:
            return 30
        else:
            return 60

    # ----------------------------
    # RETRIEVAL + FILTERING
    # ----------------------------
    def retrieve(self, user_input, recipe_type, time_limit):
        user_list = self._preprocess(user_input)
        emb = self.model.encode(user_input).tolist()

        results = self.collection.query(query_embeddings=[emb], n_results=15)
        docs = results["documents"][0]

        final = []

        for doc in docs:
            try:
                recipe_ing = doc.split("Search_Ingredients:")[1]
                instructions = doc.split("Instructions:")[1]
            except:
                recipe_ing, instructions = "", ""

            score = self._match_score(user_list, recipe_ing)
            missing = self._missing(user_list, recipe_ing)

            # FILTER: Veg/Non-Veg
            if recipe_type == "Vegetarian" and not self._is_veg(recipe_ing):
                continue

            # FILTER: Time
            est_time = self._time_estimate(instructions)
            if time_limit != "Any":
                limit = int(time_limit.split()[0])
                if est_time > limit:
                    continue

            final.append((doc, score, missing, est_time))

        return sorted(final, key=lambda x: x[1], reverse=True)[:5]

    # ----------------------------
    # GENERATION (STRUCTURED)
    # ----------------------------
    def generate(self, user_input, docs):
        context = ""

        for doc, score, missing, time in docs:
            context += f"""
{doc}
Match Score: {int(score*100)}%
Missing: {", ".join(missing) if missing else "None"}
Estimated Time: {time} mins
"""

        prompt = f"""
You are a professional cooking assistant.

User ingredients:
{user_input}

Recipes:
{context}

STRICT FORMAT (VERY IMPORTANT):

### Recipe Name
Match: XX%
Time: XX mins
Difficulty: Easy/Medium/Hard

Missing Ingredients:
- item1
- item2

Substitutions:
- item → substitute

Steps:
1. Step one
2. Step two
"""

        res = self.client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    def run(self, user_input, recipe_type, time_limit):
        docs = self.retrieve(user_input, recipe_type, time_limit)

        if not docs:
            return "❌ No recipes found. Try different ingredients or filters."

        return self.generate(user_input, docs)
