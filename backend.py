import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

load_dotenv()

class RecipeRAG:
    def __init__(self, data_path):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY missing")

        self.client = Groq(api_key=self.api_key)

        self.df = pd.read_csv(data_path)
        self.df['Search_Ingredients'] = self.df['Search_Ingredients'].fillna("")

        self.embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        if os.path.exists("chroma_db"):
            self.db = Chroma(persist_directory="chroma_db", embedding_function=self.embedding)
        else:
            docs = self.create_docs()
            self.db = Chroma.from_documents(docs, self.embedding, persist_directory="chroma_db")

        self.retriever = self.db.as_retriever(search_kwargs={"k": 10})

    def create_docs(self):
        docs = []
        for _, row in self.df.iterrows():
            content = f"""
Title: {row['Title']}
Ingredients: {row['Ingredients']}
Instructions: {row['Instructions']}
Search_Ingredients: {row['Search_Ingredients']}
"""
            docs.append(Document(page_content=content))
        return docs

    def preprocess(self, text):
        return [i.strip().lower() for i in text.split(",") if i.strip()]

    def match_score(self, user, recipe):
        recipe_list = [i.strip().lower() for i in recipe.split(",") if i.strip()]
        if not recipe_list:
            return 0
        return round(sum(1 for i in user if i in recipe_list) / len(recipe_list), 2)

    def get_missing(self, user, recipe):
        recipe_list = [i.strip().lower() for i in recipe.split(",") if i.strip()]
        return [i for i in recipe_list if i not in user]

    def apply_filters(self, docs, filter_type):
        filtered = []
        for doc, score in docs:
            text = doc.page_content.lower()

            if filter_type == "Vegetarian":
                if any(x in text for x in ["chicken", "mutton", "fish", "egg"]):
                    continue

            if filter_type == "Non-Vegetarian":
                if not any(x in text for x in ["chicken", "mutton", "fish", "egg"]):
                    continue

            filtered.append((doc, score))

        return filtered

    def retrieve(self, user_input):
        user_list = self.preprocess(user_input)
        docs = self.retriever.get_relevant_documents(user_input)

        scored = []
        for doc in docs:
            try:
                recipe_ing = doc.page_content.split("Search_Ingredients:")[1]
            except:
                recipe_ing = ""

            score = self.match_score(user_list, recipe_ing)
            missing = self.get_missing(user_list, recipe_ing)

            scored.append((doc, score, missing))

        return sorted(scored, key=lambda x: x[1], reverse=True)[:5]

    def generate(self, user_input, docs, filter_type, max_time):
        context = ""

        for doc, score, missing in docs:
            context += f"""
{doc.page_content}
Match Score: {int(score*100)}%
Missing Ingredients: {", ".join(missing) if missing else "None"}
"""

        prompt = f"""
You are an intelligent cooking assistant.

User Ingredients:
{user_input}

Filter:
Type: {filter_type}
Max Time: {max_time}

Recipes:
{context}

STRICT FORMAT:

Recipe Name:
Match Score:
Missing Ingredients:
Substitutions:
Estimated Time:
Difficulty:
Steps:

Rules:
- Always follow format
- Suggest realistic substitutions
- Keep steps short and clear
"""

        res = self.client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    def run(self, user_input, filter_type, max_time):
        docs = self.retrieve(user_input)
        docs = self.apply_filters([(d, s) for d, s, _ in docs], filter_type)

        # Re-attach missing info after filtering
        final_docs = []
        for doc, score in docs:
            recipe_ing = doc.page_content.split("Search_Ingredients:")[1]
            missing = self.get_missing(self.preprocess(user_input), recipe_ing)
            final_docs.append((doc, score, missing))

        return self.generate(user_input, final_docs, filter_type, max_time)
