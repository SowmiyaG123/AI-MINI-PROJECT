
import os, re, json, uuid, asyncio, logging, hashlib
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx, uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("recipe")

GROQ_API_KEY = "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"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama3-70b-8192"
CHROMA_DIR   = "./chroma_db"
EMBED_MODEL  = "all-MiniLM-L6-v2"

app = FastAPI(title="Recipe Assistant v4")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

RECIPES = [
    {"id":"r01","name":"Chicken Biryani","cuisine":"Indian","diet":["non-veg"],"time":"60 min","servings":4,"tags":["rice","main","spicy"],
     "ingredients":{"chicken":"500g","basmati rice":"2 cups","onion":"3","tomato":"2","yogurt":"1 cup","garlic":"6 cloves","ginger":"2 inch","biryani masala":"3 tbsp","ghee":"3 tbsp","mint":"handful","saffron":"pinch"},
     "steps":["Marinate chicken with yogurt, spices, ginger-garlic for 2 hours.","Parboil basmati rice until 70% cooked with whole spices.","Fry sliced onions in ghee until golden brown.","Cook marinated chicken with tomatoes until oil separates.","Layer rice over chicken, top with fried onions and saffron milk.","Seal pot and dum cook on low heat for 25 minutes. Mix gently and serve."]},
    {"id":"r02","name":"Butter Chicken","cuisine":"Indian","diet":["non-veg"],"time":"45 min","servings":4,"tags":["curry","main","mild"],
     "ingredients":{"chicken":"600g","butter":"4 tbsp","cream":"½ cup","tomato puree":"1 cup","onion":"2","garlic":"6 cloves","ginger":"1 inch","garam masala":"1 tsp","kashmiri chili":"2 tsp"},
     "steps":["Marinate chicken in yogurt and spices, grill until charred.","Sauté onion, garlic, ginger in butter until soft.","Add tomato puree, simmer 15 min, blend smooth.","Add grilled chicken and cream, simmer 10 min.","Finish with fenugreek leaves and butter. Serve with naan."]},
    {"id":"r03","name":"Palak Paneer","cuisine":"Indian","diet":["vegetarian"],"time":"30 min","servings":3,"tags":["curry","vegetarian","main"],
     "ingredients":{"paneer":"250g","spinach":"500g","onion":"2","tomato":"1","garlic":"4 cloves","ginger":"1 inch","cream":"2 tbsp","cumin":"1 tsp","garam masala":"½ tsp","butter":"2 tbsp"},
     "steps":["Blanch spinach 2 min, blend to smooth puree.","Sauté cumin in butter, add onion until golden.","Add ginger-garlic paste and tomato, cook down.","Pour spinach puree, season, simmer 5 min.","Add paneer cubes and cream, garam masala. Serve hot."]},
    {"id":"r04","name":"Paneer Tikka Masala","cuisine":"Indian","diet":["vegetarian"],"time":"50 min","servings":4,"tags":["curry","vegetarian","main"],
     "ingredients":{"paneer":"300g","yogurt":"½ cup","bell pepper":"2","onion":"2","tomato":"3","cream":"¼ cup","garam masala":"1.5 tsp","kashmiri chili":"1.5 tsp","garlic":"5 cloves","butter":"2 tbsp"},
     "steps":["Marinate paneer in yogurt and spices for 30 min.","Grill paneer and bell peppers until charred.","Sauté onion, garlic, tomatoes to make masala.","Blend sauce smooth, add cream and grilled paneer.","Simmer 10 min. Serve with roti."]},
    {"id":"r05","name":"Spaghetti Carbonara","cuisine":"Italian","diet":["non-veg"],"time":"25 min","servings":4,"tags":["pasta","quick","main"],
     "ingredients":{"spaghetti":"400g","pancetta":"150g","eggs":"4","parmesan":"100g","garlic":"2 cloves","black pepper":"2 tsp"},
     "steps":["Boil spaghetti al dente, reserve 1 cup pasta water.","Fry pancetta with garlic until crispy.","Whisk eggs with parmesan and generous black pepper.","Off heat, toss pasta with pancetta then egg mixture.","Add pasta water to loosen. Serve immediately."]},
    {"id":"r06","name":"Vegetable Fried Rice","cuisine":"Chinese","diet":["vegetarian","vegan"],"time":"20 min","servings":3,"tags":["rice","quick","vegetarian"],
     "ingredients":{"cooked rice":"3 cups","eggs":"3","carrot":"1","peas":"½ cup","spring onion":"4","soy sauce":"3 tbsp","garlic":"3 cloves","sesame oil":"1 tsp"},
     "steps":["Heat wok on high until smoking.","Scramble eggs, push aside. Add garlic, carrot, peas.","Add day-old rice, stir-fry breaking all clumps.","Season with soy sauce, toss with scrambled egg.","Finish with sesame oil and spring onions."]},
    {"id":"r07","name":"Chana Masala","cuisine":"Indian","diet":["vegetarian","vegan"],"time":"40 min","servings":4,"tags":["curry","vegan","main"],
     "ingredients":{"chickpeas":"2 cans","onion":"2","tomato":"3","garlic":"5 cloves","ginger":"1 inch","cumin":"1 tsp","coriander powder":"2 tsp","chana masala":"2 tsp","oil":"3 tbsp"},
     "steps":["Sauté cumin and onion until golden.","Add ginger-garlic paste and tomatoes, cook until oil separates.","Add spices and drained chickpeas with 1 cup water.","Simmer 20 min.","Mash a few chickpeas to thicken. Garnish with cilantro and lemon."]},
    {"id":"r08","name":"Grilled Salmon","cuisine":"Mediterranean","diet":["non-veg","pescatarian"],"time":"20 min","servings":4,"tags":["seafood","quick","healthy"],
     "ingredients":{"salmon fillet":"4 pieces","butter":"3 tbsp","lemon":"2","garlic":"3 cloves","dill":"handful","olive oil":"2 tbsp"},
     "steps":["Pat salmon dry, season with salt and pepper.","Grill 4 min per side on oiled pan.","Melt butter, add minced garlic for 1 min.","Add lemon juice and fresh dill.","Spoon butter sauce over salmon. Serve immediately."]},
    {"id":"r09","name":"Mushroom Risotto","cuisine":"Italian","diet":["vegetarian"],"time":"35 min","servings":4,"tags":["rice","vegetarian","main"],
     "ingredients":{"arborio rice":"1.5 cups","mushrooms":"300g","onion":"1","garlic":"3 cloves","white wine":"½ cup","parmesan":"80g","butter":"4 tbsp","vegetable stock":"5 cups"},
     "steps":["Keep vegetable stock warm in a separate pot.","Sauté mushrooms golden, set aside.","Cook onion and garlic in butter, add arborio rice.","Add wine, then stock one ladle at a time, stirring constantly.","After 18 min, stir in mushrooms, parmesan, and remaining butter."]},
    {"id":"r10","name":"Dal Makhani","cuisine":"Indian","diet":["vegetarian"],"time":"90 min","servings":4,"tags":["lentils","vegetarian","main"],
     "ingredients":{"black lentils":"1 cup","kidney beans":"¼ cup","butter":"3 tbsp","cream":"¼ cup","tomato puree":"1 cup","onion":"2","garlic":"5 cloves","garam masala":"1 tsp"},
     "steps":["Soak lentils overnight, pressure cook 45 min until very soft.","Sauté onion golden, add garlic, spices, tomato puree.","Combine lentils with masala, simmer 20 min stirring often.","Add cream and butter, slow cook 10 more minutes.","Serve with butter naan."]},
    {"id":"r11","name":"Thai Green Curry","cuisine":"Thai","diet":["non-veg"],"time":"30 min","servings":4,"tags":["curry","spicy","main"],
     "ingredients":{"chicken":"400g","coconut milk":"400ml","green curry paste":"3 tbsp","bell pepper":"1","fish sauce":"2 tbsp","basil":"handful","zucchini":"1"},
     "steps":["Fry green curry paste in oil 1 min until fragrant.","Add coconut milk, bring to simmer.","Add chicken, cook through, then add vegetables.","Season with fish sauce and a pinch of sugar.","Finish with basil and lime leaves. Serve with jasmine rice."]},
    {"id":"r12","name":"Apple Crumble","cuisine":"British","diet":["vegetarian"],"time":"45 min","servings":6,"tags":["dessert","baked","sweet"],
     "ingredients":{"apple":"4 large","sugar":"4 tbsp","cinnamon":"1 tsp","lemon":"1","flour":"1 cup","butter":"80g","oats":"½ cup","brown sugar":"3 tbsp"},
     "steps":["Peel and slice apples, toss with sugar, cinnamon, lemon juice.","Spread apple mixture in baking dish.","Rub cold butter into flour, oats, brown sugar until crumbly.","Spread crumble topping over apples.","Bake at 180C for 30 min until golden and bubbling."]},
    {"id":"r13","name":"Apple Cinnamon Pancakes","cuisine":"American","diet":["vegetarian"],"time":"25 min","servings":4,"tags":["breakfast","sweet","quick"],
     "ingredients":{"apple":"2","flour":"1.5 cups","eggs":"2","milk":"1 cup","sugar":"2 tbsp","cinnamon":"1 tsp","baking powder":"2 tsp","butter":"2 tbsp","vanilla extract":"1 tsp"},
     "steps":["Grate apple finely. Mix all dry ingredients in bowl.","Whisk eggs, milk, vanilla, and melted butter.","Fold wet into dry, add grated apple — do not overmix.","Cook pancakes on medium heat 2-3 min per side until golden.","Serve with maple syrup and extra sliced apple."]},
    {"id":"r14","name":"Apple Smoothie","cuisine":"Western","diet":["vegetarian","vegan"],"time":"5 min","servings":2,"tags":["drink","healthy","quick"],
     "ingredients":{"apple":"2","banana":"1","milk":"1 cup","honey":"1 tbsp","cinnamon":"pinch","ice cubes":"6"},
     "steps":["Core and chop apple.","Add all ingredients to blender.","Blend on high until completely smooth.","Adjust sweetness with honey.","Pour into glasses and serve chilled."]},
    {"id":"r15","name":"Apple Ice Cream Sundae","cuisine":"American","diet":["vegetarian"],"time":"10 min","servings":2,"tags":["dessert","sweet","quick"],
     "ingredients":{"apple":"1","vanilla ice cream":"3 scoops","caramel sauce":"2 tbsp","whipped cream":"¼ cup","cinnamon":"pinch","butter":"1 tbsp"},
     "steps":["Slice apple thin, sauté in butter with a pinch of sugar for 3 min.","Scoop ice cream into a serving bowl.","Top with warm caramel apple slices.","Add whipped cream.","Dust with cinnamon and serve immediately."]},
    {"id":"r16","name":"Mango Lassi","cuisine":"Indian","diet":["vegetarian"],"time":"5 min","servings":2,"tags":["drink","sweet","quick"],
     "ingredients":{"mango":"2 ripe","yogurt":"1 cup","milk":"½ cup","sugar":"2 tbsp","cardamom":"pinch","ice cubes":"6"},
     "steps":["Blend mango pulp until smooth.","Add yogurt, milk, sugar, and cardamom.","Blend with ice until frothy.","Taste and adjust sweetness.","Serve chilled in tall glasses."]},
    {"id":"r17","name":"Classic Omelette","cuisine":"French","diet":["vegetarian"],"time":"5 min","servings":1,"tags":["breakfast","quick","egg"],
     "ingredients":{"eggs":"3","butter":"1 tbsp","salt":"pinch","black pepper":"pinch"},
     "steps":["Beat eggs with salt and pepper until combined.","Melt butter in non-stick pan until foamy.","Pour eggs, stir gently while shaking pan.","Fold when edges are set but center is still soft.","Slide out immediately onto plate."]},
    {"id":"r18","name":"Shakshuka","cuisine":"Middle Eastern","diet":["vegetarian"],"time":"30 min","servings":3,"tags":["breakfast","egg","spicy"],
     "ingredients":{"eggs":"4","canned tomatoes":"400g","bell pepper":"1","onion":"1","garlic":"4 cloves","cumin":"1 tsp","paprika":"1 tsp","olive oil":"2 tbsp"},
     "steps":["Sauté onion and bell pepper in olive oil until soft.","Add garlic and spices, cook 1 min.","Pour in canned tomatoes, simmer 10 min until thick.","Make 4 wells, crack in eggs, cover and cook 5-8 min.","Serve with crusty bread."]},
    {"id":"r19","name":"Pesto Pasta","cuisine":"Italian","diet":["vegetarian"],"time":"20 min","servings":4,"tags":["pasta","vegetarian","quick"],
     "ingredients":{"pasta":"400g","basil":"2 cups","pine nuts":"3 tbsp","parmesan":"60g","garlic":"2 cloves","olive oil":"½ cup"},
     "steps":["Boil pasta al dente, reserve half cup pasta water.","Blend basil, pine nuts, garlic, parmesan until smooth.","Drizzle olive oil while blending. Season.","Toss hot pasta with pesto, adding pasta water to loosen.","Serve immediately with extra parmesan."]},
    {"id":"r20","name":"Avocado Toast","cuisine":"Western","diet":["vegetarian"],"time":"10 min","servings":2,"tags":["breakfast","quick","healthy"],
     "ingredients":{"avocado":"1","bread":"2 slices","eggs":"2","lemon":"½","chili flakes":"pinch"},
     "steps":["Toast bread until golden and crisp.","Mash avocado with lemon juice, salt, and pepper.","Poach eggs in simmering water for 3 min.","Spread avocado on toast.","Top with poached egg, chili flakes, and lemon."]},
    {"id":"r21","name":"Egg Fried Rice","cuisine":"Chinese","diet":["vegetarian"],"time":"15 min","servings":2,"tags":["rice","quick","egg"],
     "ingredients":{"cooked rice":"2 cups","eggs":"3","soy sauce":"2 tbsp","garlic":"2 cloves","spring onion":"3","sesame oil":"1 tsp","oil":"1 tbsp"},
     "steps":["Heat oil in wok on high.","Scramble eggs until just set, set aside.","Add garlic and rice, stir-fry 3 min breaking clumps.","Add soy sauce and eggs back, toss well.","Finish with sesame oil and spring onion."]},
    {"id":"r22","name":"Chicken Soup","cuisine":"American","diet":["non-veg"],"time":"50 min","servings":6,"tags":["soup","comfort","healthy"],
     "ingredients":{"chicken":"500g","carrot":"3","celery":"3 stalks","onion":"1","garlic":"4 cloves","chicken broth":"6 cups","egg noodles":"200g","thyme":"4 sprigs"},
     "steps":["Simmer chicken in broth with thyme for 30 min.","Remove chicken, shred meat, discard bones.","Sauté onion, celery, carrot in same pot.","Return broth and chicken, add noodles.","Cook noodles until tender. Season and serve."]},
    {"id":"r23","name":"Beef Tacos","cuisine":"Mexican","diet":["non-veg"],"time":"25 min","servings":4,"tags":["main","quick","street food"],
     "ingredients":{"ground beef":"500g","taco shells":"8","onion":"1","garlic":"3 cloves","cumin":"1 tsp","chili powder":"1.5 tsp","tomato":"2","cheddar cheese":"100g","sour cream":"4 tbsp","lime":"1"},
     "steps":["Brown ground beef with onion and garlic.","Add cumin, chili powder, salt and cook 2 min.","Warm taco shells in oven at 180C for 3 min.","Fill shells with beef, tomato, cheese, sour cream.","Squeeze lime juice and serve."]},
    {"id":"r24","name":"Tomato Soup","cuisine":"Western","diet":["vegetarian","vegan"],"time":"30 min","servings":4,"tags":["soup","vegan","comfort"],
     "ingredients":{"tomato":"8 large","onion":"1","garlic":"4 cloves","vegetable stock":"2 cups","olive oil":"2 tbsp","basil":"handful","sugar":"1 tsp"},
     "steps":["Roast tomatoes and garlic with olive oil at 200C for 20 min.","Sauté onion until soft.","Add roasted tomatoes and stock, simmer 10 min.","Blend until completely smooth.","Season, garnish with basil."]},
    {"id":"r25","name":"Margherita Pizza","cuisine":"Italian","diet":["vegetarian"],"time":"25 min","servings":2,"tags":["main","baked","vegetarian"],
     "ingredients":{"pizza dough":"300g","tomato sauce":"½ cup","mozzarella":"200g","fresh basil":"handful","olive oil":"2 tbsp","garlic":"1 clove"},
     "steps":["Preheat oven to 250C with baking stone.","Stretch dough to 30cm circle.","Spread thin tomato sauce, leaving 1cm border.","Tear mozzarella over sauce, drizzle olive oil.","Bake 10-12 min until crust golden. Top with basil."]},
]

SUBS = {
    "paneer":["firm tofu (1:1, press dry first — vegan)","halloumi (1:1, saltier)","chicken breast (1:1, non-veg)"],
    "chicken":["turkey (1:1, leaner)","firm tofu (1:1, vegan)","paneer (1:1, vegetarian)","chickpeas (1 cup per 200g)"],
    "beef":["lamb (1:1, richer)","portobello mushroom (1:1, vegan)","jackfruit (1:1, vegan pulled)"],
    "butter":["ghee (3/4:1, higher smoke point)","coconut oil (3/4:1, vegan)","olive oil (3/4:1)"],
    "cream":["coconut cream (1:1, vegan)","cashew cream (1:1)","Greek yogurt (1:1, reduce heat)"],
    "eggs":["flax egg (1 tbsp ground flax + 3 tbsp water)","chia egg (same ratio)","silken tofu (1/4 cup per egg)"],
    "milk":["oat milk (1:1)","almond milk (1:1)","soy milk (1:1)","coconut milk (1:1, richer)"],
    "apple":["pear (1:1)","peach (1:1, softer)","quince (1:1, more tart)"],
    "mango":["peach (1:1)","papaya (1:1)","apple (1:1, less sweet)"],
    "vanilla ice cream":["gelato (1:1, denser)","frozen yogurt (1:1, tangier)","coconut ice cream (1:1, vegan)"],
    "yogurt":["sour cream (1:1)","coconut yogurt (1:1, vegan)","buttermilk (3/4:1, thinner)"],
    "salmon":["tuna steak (1:1)","cod (1:1, milder)","firm tofu (1:1, vegan)"],
    "pasta":["spaghetti/penne/fusilli (1:1)","zucchini noodles (1:1, low-carb)","rice noodles (1:1, gluten-free)"],
    "parmesan":["pecorino romano (1:1, sharper)","nutritional yeast (2 tbsp per 30g, vegan)"],
    "garlic":["garlic powder (1/8 tsp per clove)","shallots (1 small per clove)"],
    "coconut milk":["cashew cream (1:1)","heavy cream (1:1)","oat cream (1:1)"],
    "spinach":["kale (1:1, cook longer)","swiss chard (1:1)","frozen spinach (half weight, squeeze dry)"],
    "chickpeas":["white beans (1:1)","lentils (1:1)","edamame (1:1)"],
    "rice":["quinoa (1:1, more protein)","cauliflower rice (1:1, low-carb)","couscous (1:1, faster)"],
    "soy sauce":["tamari (1:1, gluten-free)","coconut aminos (1:1, less salty)"],
}

ING_MAP = {
    "chicken":["chicken","boneless chicken","chicken breast","chicken thigh","chicken pieces","chicken drumstick","grilled chicken","rotisserie chicken"],
    "beef":["beef","ground beef","minced beef","beef steak","beef mince"],
    "pork":["pork","ground pork","pork belly","pork chop","bacon"],
    "salmon":["salmon","salmon fillet","smoked salmon","atlantic salmon"],
    "eggs":["eggs","egg","egg yolk","egg white","boiled egg"],
    "milk":["milk","whole milk","skim milk","full fat milk"],
    "butter":["butter","unsalted butter","salted butter"],
    "cream":["cream","heavy cream","double cream","whipping cream","fresh cream"],
    "tomato":["tomato","tomatoes","cherry tomatoes","roma tomatoes","canned tomatoes","tomato puree","tomato paste","crushed tomatoes","tinned tomatoes"],
    "onion":["onion","onions","red onion","white onion","yellow onion","spring onion","shallot","green onion","scallion"],
    "garlic":["garlic","garlic cloves","minced garlic","garlic paste","garlic powder"],
    "ginger":["ginger","fresh ginger","ginger paste","ground ginger","ginger root"],
    "paneer":["paneer","cottage cheese"],
    "rice":["rice","basmati rice","cooked rice","jasmine rice","arborio rice","white rice","brown rice","leftover rice"],
    "pasta":["pasta","spaghetti","penne","fettuccine","linguine","rigatoni","farfalle","fusilli","noodles"],
    "mushrooms":["mushrooms","mushroom","portobello","button mushrooms","cremini","shiitake","oyster mushroom"],
    "spinach":["spinach","baby spinach","fresh spinach","frozen spinach","palak"],
    "apple":["apple","apples","green apple","red apple","granny smith","apple slices"],
    "mango":["mango","mangoes","mango pulp","alphonso","raw mango"],
    "lemon":["lemon","lime","lemon juice","lime juice","citrus","lemon zest"],
    "vanilla ice cream":["vanilla ice cream","ice cream","vanilla icecream","ice-cream"],
    "coconut milk":["coconut milk","coconut cream","full fat coconut milk"],
    "yogurt":["yogurt","curd","greek yogurt","plain yogurt","dahi","hung curd"],
    "chickpeas":["chickpeas","chana","garbanzo beans","canned chickpeas","dried chickpeas"],
    "bell pepper":["bell pepper","capsicum","red pepper","green pepper","yellow pepper","paprika pepper"],
    "bread":["bread","sandwich bread","sourdough","baguette","whole wheat bread","white bread","toast"],
    "avocado":["avocado","avocados","ripe avocado"],
    "cheese":["cheese","cheddar","mozzarella","parmesan","feta","gouda","brie","parmesan cheese"],
    "flour":["flour","all purpose flour","plain flour","wheat flour","maida"],
    "sugar":["sugar","granulated sugar","white sugar","brown sugar","caster sugar","powdered sugar"],
    "oil":["oil","vegetable oil","cooking oil","sunflower oil","canola oil"],
    "olive oil":["olive oil","extra virgin olive oil","EVOO"],
    "soy sauce":["soy sauce","soya sauce","light soy sauce","dark soy sauce"],
    "cumin":["cumin","cumin seeds","jeera","ground cumin"],
    "cinnamon":["cinnamon","ground cinnamon","cinnamon stick","cinnamon powder"],
    "black pepper":["black pepper","pepper","ground pepper","cracked pepper","white pepper"],
    "salt":["salt","sea salt","kosher salt","table salt","rock salt"],
    "carrot":["carrot","carrots","baby carrots","shredded carrot"],
    "potato":["potato","potatoes","baby potatoes","sweet potato","aloo"],
    "banana":["banana","bananas","ripe banana","plantain"],
    "ghee":["ghee","clarified butter","desi ghee"],
    "turmeric":["turmeric","haldi","ground turmeric","turmeric powder"],
    "garam masala":["garam masala","mixed spice","garam masala powder"],
    "biryani masala":["biryani masala","biryani spice mix"],
    "green curry paste":["green curry paste","thai green curry paste"],
    "saffron":["saffron","kesar","saffron strands"],
    "mint":["mint","fresh mint","mint leaves","pudina"],
    "basil":["basil","fresh basil","thai basil","basil leaves"],
    "dill":["dill","fresh dill","dill weed"],
    "pine nuts":["pine nuts","pignoli"],
    "oats":["oats","rolled oats","oatmeal","porridge oats"],
    "honey":["honey","raw honey","organic honey"],
    "caramel sauce":["caramel sauce","caramel","toffee sauce"],
    "whipped cream":["whipped cream","whipping cream","double cream"],
    "cardamom":["cardamom","green cardamom","cardamom powder","elaichi"],
    "peas":["peas","green peas","frozen peas","fresh peas"],
    "sesame oil":["sesame oil","toasted sesame oil","asian sesame oil"],
    "spring onion":["spring onion","scallion","green onion","chives"],
    "baking powder":["baking powder","raising agent"],
    "vanilla extract":["vanilla extract","vanilla essence","vanilla"],
    "white wine":["white wine","dry white wine","cooking wine"],
    "vegetable stock":["vegetable stock","veggie broth","vegetable broth"],
    "chicken broth":["chicken broth","chicken stock","chicken bouillon"],
    "fish sauce":["fish sauce","nam pla","thai fish sauce"],
    "kidney beans":["kidney beans","rajma","canned kidney beans"],
    "black lentils":["black lentils","urad dal","whole urad","black gram"],
    "pancetta":["pancetta","bacon","lardons","streaky bacon"],
    "ground beef":["ground beef","minced beef","beef mince"],
    "taco shells":["taco shells","tortillas","hard taco shells"],
}

CANONICAL: dict[str, str] = {}
for canon, variants in ING_MAP.items():
    for v in variants:
        CANONICAL[v.lower().strip()] = canon

SESSIONS: dict[str, dict] = {}
_chroma_col = None
_embed_mdl  = None

def get_chroma():
    global _chroma_col, _embed_mdl
    if _chroma_col is not None:
        return _chroma_col
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        col    = client.get_or_create_collection("recipes_v4", metadata={"hnsw:space":"cosine"})
        dset_hash = hashlib.md5(json.dumps([r["id"] for r in RECIPES]).encode()).hexdigest()
        already = False
        if col.count() > 0:
            try:
                meta = col.get(ids=["__meta__"], include=["metadatas"])
                already = meta["metadatas"] and meta["metadatas"][0].get("h") == dset_hash
            except Exception:
                pass
        if not already:
            log.info("Building embeddings (one-time)…")
            mdl = SentenceTransformer(EMBED_MODEL)
            _embed_mdl = mdl
            texts = [f"{r['name']} {r['cuisine']} {' '.join(r['tags'])} {' '.join(r['ingredients'].keys())} {' '.join(r['steps'])}" for r in RECIPES]
            embs  = mdl.encode(texts, normalize_embeddings=True).tolist()
            col.upsert(documents=texts, embeddings=embs, ids=[r["id"] for r in RECIPES],
                       metadatas=[{"name":r["name"]} for r in RECIPES])
            col.upsert(documents=["__meta__"], ids=["__meta__"], metadatas=[{"h":dset_hash}])
            log.info("Embeddings persisted to ./chroma_db — will NOT re-run on next start")
        else:
            log.info("Cached embeddings loaded from ./chroma_db")
            _embed_mdl = SentenceTransformer(EMBED_MODEL)
        _chroma_col = col
        return col
    except Exception as e:
        log.warning(f"ChromaDB unavailable ({e}) — keyword-only mode")
        return None

def sem_scores(query: str) -> dict[str, float]:
    col = get_chroma()
    if col is None or _embed_mdl is None: return {}
    try:
        q_emb = _embed_mdl.encode([query], normalize_embeddings=True).tolist()
        res = col.query(query_embeddings=q_emb, n_results=min(len(RECIPES), 25),
                        where={"name":{"$ne":"__meta__"}})
        return {rid: 1.0 - dist for rid, dist in zip(res["ids"][0], res["distances"][0])}
    except Exception:
        return {}

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())

def canonicalize(raw: str) -> str:
    r = norm(raw)
    if r in CANONICAL: return CANONICAL[r]
    for canon, variants in ING_MAP.items():
        for v in variants:
            if norm(v) == r or (len(r) > 3 and (r in norm(v) or norm(v) in r)):
                return canon
    return r

_ALL_TOKENS = sorted(
    {norm(v) for variants in ING_MAP.values() for v in variants}
    | {norm(k) for r in RECIPES for k in r["ingredients"]}
    | set(ING_MAP.keys()),
    key=len, reverse=True
)

NOISE = {"i","have","want","make","cook","need","some","the","and","with","for","a","an","me",
         "please","can","my","is","no","any","all","do","what","give","suggest","show","recipes",
         "recipe","dish","food","using","want","would","like","also","but","not","only","just",
         "cup","cups","tbsp","tsp","grams","kg","ml","liter","few","some","bit","little"}

def extract_ingredients(text: str) -> list[str]:
    t = norm(text)
    found_raw = []
    # Pass 1: greedy longest-match on known tokens
    for token in _ALL_TOKENS:
        pat = r'(?<![a-z])' + re.escape(token) + r'(?![a-z])'
        if re.search(pat, t):
            found_raw.append(token)
            t = re.sub(pat, " " * len(token), t)
    # Pass 2: comma/and fallback for leftover text
    remaining = re.sub(r"[^a-z,& ]+", " ", t)
    for part in re.split(r"[,&]| and ", remaining):
        part = part.strip()
        if part and len(part) > 2 and part not in NOISE and not part.isdigit():
            found_raw.append(part)
    seen, out = set(), []
    for raw in found_raw:
        c = canonicalize(raw)
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out

async def groq_nlu(text: str, history: list) -> dict:
    system = """You are an intent classifier for a Recipe Assistant. Extract a JSON object:
{
  "intent": "find_recipe"|"substitution"|"set_preference"|"greeting"|"help"|"thanks"|"small_talk",
  "ingredients": [list of ingredients user HAS/WANTS TO USE],
  "exclude": [ingredients user does NOT want],
  "diet": [vegetarian|vegan|pescatarian|halal|gluten-free],
  "meal_type": "breakfast"|"lunch"|"dinner"|"dessert"|"drink"|"snack"|null,
  "cuisine": "Indian"|"Italian"|"Chinese"|"Thai"|"Mexican"|null,
  "query_for_search": "refined search string"
}
Rules: "no X" / "without X" / "don't eat X" → exclude:[X]. "I have X,Y,Z" → ingredients:[X,Y,Z]. ONLY JSON, no extra text."""
    messages = [{"role":"system","content":system}]
    for h in history[-4:]:
        messages.append({"role":h["role"],"content":h["content"]})
    messages.append({"role":"user","content":text})
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.post(GROQ_URL, headers={"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"},
                json={"model":GROQ_MODEL,"messages":messages,"max_tokens":300,"temperature":0})
            if r.status_code == 200:
                raw = r.json()["choices"][0]["message"]["content"].strip()
                raw = re.sub(r"^```json|```$","",raw,flags=re.MULTILINE).strip()
                return json.loads(raw)
    except Exception as e:
        log.warning(f"Groq NLU failed: {e}")
    return _rule_nlu(text)

def _rule_nlu(text: str) -> dict:
    t = norm(text)
    intent = "find_recipe"
    if re.search(r"^(hi|hello|hey)\b", t): intent = "greeting"
    elif re.search(r"\b(help|what can you)\b", t): intent = "help"
    elif re.search(r"\b(thank|awesome|great)\b", t): intent = "thanks"
    elif re.search(r"\b(substitute|replace|instead of|alternative)\b", t): intent = "substitution"
    elif re.search(r"\b(no |don.t eat|avoid|i am vegetarian|i.m vegan)\b", t): intent = "set_preference"
    exclude = []
    for m in re.finditer(r"\bno\s+(\w+)\b|\bwithout\s+(\w+)\b|\bavoid\s+(\w+)\b|\bdon.?t (?:want|eat)\s+(\w+)\b", t):
        item = next((g for g in m.groups() if g), None)
        if item: exclude.append(item)
    diet = [d for d in ["vegetarian","vegan","pescatarian","halal","gluten-free"] if d in t]
    meal = next((m for m in ["breakfast","lunch","dinner","dessert","drink","snack"] if m in t), None)
    return {"intent":intent,"ingredients":extract_ingredients(t),"exclude":exclude,"diet":diet,
            "meal_type":meal,"cuisine":None,"query_for_search":text}

async def groq_explain(recipe: dict, user_ings: list, missing: list) -> str:
    try:
        prompt = f"""User has: {', '.join(user_ings) if user_ings else 'general query'}.
Top recipe: {recipe['name']} ({recipe['cuisine']}, {recipe['time']}).
Write ONE warm sentence (max 18 words) explaining why this is the best match. No markdown."""
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.post(GROQ_URL, headers={"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"},
                json={"model":GROQ_MODEL,"messages":[{"role":"user","content":prompt}],"max_tokens":50,"temperature":0.3})
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    matched_count = len(set(user_ings) & {canonicalize(norm(k)) for k in recipe["ingredients"]})
    return f"Uses {matched_count} of your ingredients and matches your query perfectly."

def score_recipe(recipe: dict, user_ings: list, exclude: list, sscores: dict, query: str) -> tuple[float, list]:
    r_canonical = {canonicalize(norm(k)) for k in recipe["ingredients"]}
    excl_canon  = {canonicalize(norm(e)) for e in exclude}

    # HARD FILTER: excluded ingredient present
    if r_canonical & excl_canon:
        return -1.0, []

    q = norm(query)
    user_canon = set(user_ings)

    # NO INGREDIENTS: keyword mode
    if not user_canon:
        name_words = [w for w in norm(recipe["name"]).split() if len(w) > 2]
        kw  = sum(1 for w in name_words if w in q) / max(len(name_words), 1)
        tag = sum(0.08 for tag in recipe.get("tags",[]) if tag in q)
        sem = sscores.get(recipe["id"], 0.0) * 0.25
        return min(1.0, kw*0.6 + tag + sem), []

    main_ing = user_ings[0] if user_ings else None

    # HARD CHECK: main ingredient must be in recipe (exact or partial)
    if main_ing:
        main_exact   = main_ing in r_canonical
        main_partial = any(main_ing in norm(k) or norm(k) in main_ing for k in recipe["ingredients"])
        main_in_name = main_ing in norm(recipe["name"])
        if not main_exact and not main_partial and not main_in_name:
            return 0.0, []

    # Ingredient overlap (with partial matching)
    matched = set()
    for u in user_canon:
        if u in r_canonical:
            matched.add(u)
        else:
            for rc in r_canonical:
                if (u in rc or rc in u) and len(u) > 2:
                    matched.add(u)
                    break

    missing   = sorted(r_canonical - user_canon)[:5]
    overlap   = len(matched) / max(len(r_canonical), 1)
    # Name boost: ingredient in recipe name = very strong signal
    name_boost = min(0.3, sum(0.15 for u in user_canon if u in norm(recipe["name"])))
    # Tag/cuisine keyword boost
    kw_boost   = sum(0.04 for tag in recipe.get("tags",[]) if tag in q)
    if recipe.get("cuisine") and norm(recipe["cuisine"]) in q: kw_boost += 0.05
    # Semantic as small tiebreaker (10%)
    sem = sscores.get(recipe["id"], 0.0) * 0.10

    final = min(1.0, overlap*0.70 + name_boost*0.20 + sem + kw_boost)

    # Additional boost if main ingredient is literally in the recipe name
    if main_ing and main_ing in norm(recipe["name"]):
        final = min(1.0, final + 0.15)

    return final, missing

def hybrid_search(query: str, user_ings: list, nlu: dict, top_k: int = 5) -> list[dict]:
    exclude = [canonicalize(norm(e)) for e in nlu.get("exclude", [])]
    sscores = sem_scores(query)
    results = []
    for r in RECIPES:
        sc, miss = score_recipe(r, user_ings, exclude, sscores, query)
        if sc <= 0: continue
        mp = min(99, round(100 * sc)) if user_ings else None
        results.append({"recipe":r,"score":sc,"missing":miss,"match_pct":mp})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def find_sub(text: str, nlu: dict) -> Optional[str]:
    for ing in nlu.get("ingredients",[]):
        c = canonicalize(norm(ing))
        if c in SUBS: return c
    t = norm(text)
    for pat in [r"substitute (?:for )?([a-z ]+?)(?:\?|$|,|\band\b)",
                r"replace (?:the )?([a-z ]+?)(?:\?|$|,)",
                r"instead of ([a-z ]+?)(?:\?|$|,)",
                r"without ([a-z ]+?)(?:\?|$|,)",
                r"alternative (?:to|for) ([a-z ]+?)(?:\?|$)"]:
        m = re.search(pat, t)
        if m:
            c = canonicalize(m.group(1).strip())
            if c in SUBS: return c
    for k in SUBS:
        if k in t: return k
    return None

def get_sess(sid: str) -> dict:
    if sid not in SESSIONS:
        SESSIONS[sid] = {"exclude":[],"diet":[],"cuisine":[],"history":[]}
    return SESSIONS[sid]

def merge_prefs(sess: dict, nlu: dict):
    for e in nlu.get("exclude",[]):
        c = canonicalize(norm(e))
        if c not in sess["exclude"]: sess["exclude"].append(c)
    for d in nlu.get("diet",[]):
        if d not in sess["diet"]: sess["diet"].append(d)

async def handle(text: str, sess: dict) -> dict:
    nlu = await groq_nlu(text, sess["history"])
    merge_prefs(sess, nlu)
    intent = nlu.get("intent","find_recipe")
    search_query = nlu.get("query_for_search", text)
    nlu_ings  = [canonicalize(norm(i)) for i in nlu.get("ingredients",[])]
    rule_ings = extract_ingredients(text)
    user_ings = list(dict.fromkeys(nlu_ings + [i for i in rule_ings if i not in nlu_ings]))
    nlu["exclude"] = list(set(nlu.get("exclude",[]) + sess["exclude"]))

    if intent == "greeting":
        return {"type":"greeting","message":"👋 Hey! I'm your AI Recipe Assistant.\n\nTell me what ingredients you have and I'll find the best recipes for you. Try:\n• *'I have chicken, rice and tomatoes'*\n• *'No beef, I'm vegetarian'*\n• *'Substitute for paneer'*","recipes":[],"sub":None}
    if intent == "help":
        return {"type":"help","message":"🍳 **What I can do:**\n• Find recipes from your ingredients (exact + semantic matching)\n• Enforce dietary restrictions strictly\n• Suggest ingredient substitutes\n• Remember your preferences all session\n• Scan ingredient photos via 📷","recipes":[],"sub":None}
    if intent == "thanks":
        return {"type":"thanks","message":"😊 Happy cooking! Ask me anything else.","recipes":[],"sub":None}
    if intent == "substitution":
        target = find_sub(text, nlu)
        if target and target in SUBS:
            return {"type":"sub","message":f"🔄 Best substitutes for **{target}**:","recipes":[],"sub":{"ingredient":target,"options":SUBS[target]}}
        for ing in user_ings:
            if ing in SUBS:
                return {"type":"sub","message":f"🔄 Substitutes for **{ing}**:","recipes":[],"sub":{"ingredient":ing,"options":SUBS[ing]}}
        return {"type":"sub","message":"Couldn't identify the ingredient. Try: *'substitute for paneer'*","recipes":[],"sub":None}
    if intent == "set_preference" and not user_ings:
        excl = sess["exclude"]; diets = sess["diet"]
        parts = ([f"excluding **{', '.join(excl)}**"] if excl else []) + ([f"**{', '.join(diets)}** diet"] if diets else [])
        return {"type":"pref","message":"✅ Preferences saved: " + (", ".join(parts) or "none") + ".\n\nNow tell me what ingredients you have!","recipes":[],"sub":None}

    hits = hybrid_search(search_query, user_ings, nlu)
    if not hits:
        excl_str = f" excluding **{', '.join(nlu['exclude'])}**" if nlu.get("exclude") else ""
        return {"type":"no_result","message":f"😔 No matching recipes found{excl_str}.\n\nTry different ingredients or relax constraints.","recipes":[],"sub":None}

    top = hits[0]; r = top["recipe"]
    explanation = await groq_explain(r, user_ings, top["missing"])
    ing_str = f" using **{', '.join(user_ings)}**" if user_ings else ""
    pct_str = f" ({top['match_pct']}% ingredient match)" if top["match_pct"] is not None else ""
    msg = f"🍽️ Found **{len(hits)} recipe{'s' if len(hits)>1 else ''}**{ing_str}{pct_str}!\n\n💡 {explanation}"
    if top["missing"]: msg += f"\n\n⚠️ Top recipe also needs: **{', '.join(top['missing'][:4])}**"
    if sess.get("exclude"): msg += f"\n✅ Excluded: **{', '.join(sess['exclude'])}**"

    cards = []
    for h in hits:
        rec = h["recipe"]
        r_canon = {canonicalize(norm(k)) for k in rec["ingredients"]}
        matched = [i for i in user_ings if i in r_canon or any(i in norm(k) or norm(k) in i for k in rec["ingredients"])]
        cards.append({"id":rec["id"],"name":rec["name"],"cuisine":rec["cuisine"],"diet":rec["diet"],
                      "time":rec["time"],"servings":rec["servings"],"tags":rec.get("tags",[]),
                      "ingredients":rec["ingredients"],"steps":rec["steps"],
                      "match_pct":h["match_pct"],"missing":h["missing"],"matched_ingredients":matched})
    return {"type":"recipes","message":msg,"recipes":cards,"sub":None}

class ChatReq(BaseModel):
    session_id: str = ""
    message: str

@app.on_event("startup")
async def startup():
    asyncio.create_task(asyncio.to_thread(get_chroma))

@app.post("/chat")
async def chat(req: ChatReq):
    sid  = req.session_id or str(uuid.uuid4())
    sess = get_sess(sid)
    sess["history"].append({"role":"user","content":req.message})
    result = await handle(req.message, sess)
    sess["history"].append({"role":"assistant","content":result["message"]})
    return {**result,"session_id":sid,"preferences":{"exclude":sess["exclude"],"diet":sess["diet"]}}

@app.post("/ocr")
async def ocr(file: UploadFile = File(...), session_id: str = "default"):
    content = await file.read()
    detected = []
    try:
        from PIL import Image
        import pytesseract, io
        img  = Image.open(io.BytesIO(content)).convert("L")
        text = pytesseract.image_to_string(img, config="--psm 6")
        detected = extract_ingredients(text)
    except Exception as e:
        log.warning(f"OCR: {e}")
    if not detected:
        return {"session_id":session_id,"detected":[],"message":"No ingredients detected. Please type them instead.","recipes":[]}
    sess   = get_sess(session_id)
    result = await handle("recipes with " + " ".join(detected), sess)
    return {"session_id":session_id,"detected":detected,
            "message":f"Detected: **{', '.join(detected)}**\n\n" + result["message"],"recipes":result["recipes"]}

@app.post("/reset")
async def reset(body: dict):
    sid = body.get("session_id","")
    if sid in SESSIONS: del SESSIONS[sid]
    return {"status":"reset"}

@app.get("/health")
def health():
    return {"status":"ok","recipes":len(RECIPES),"substitutions":len(SUBS),
            "chroma":"ready" if _chroma_col else "loading","groq":"configured"}
@app.get("/")
def home(): 
    return {"status": "online", "engine": "Pro Chef AI"}
if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=False)
