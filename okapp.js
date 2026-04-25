import React, { useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

function App() {
  const [query, setQuery] = useState("");
  const [recipes, setRecipes] = useState([]);
  const [veg, setVeg] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [image, setImage] = useState(null);

 const search = async () => {
  try {
    const res = await axios.post(`${API}/chat`, {
      query,
      veg,
      difficulty
    });

    setRecipes(res.data.recipes || []);
  } catch (err) {
    console.error("API ERROR:", err);
    alert("Backend not reachable");
  }
};

  const upload = async () => {
    const formData = new FormData();
    formData.append("file", image);

    const res = await axios.post(`${API}/upload`, formData);
    setRecipes(res.data.recipes || []);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>🍳 Recipe Assistant Pro</h2>

      <input
        placeholder="Enter ingredients..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <select onChange={(e) => setVeg(e.target.value)}>
        <option value="">All</option>
        <option value="Veg">Veg</option>
        <option value="Non-Veg">Non-Veg</option>
      </select>

      <select onChange={(e) => setDifficulty(e.target.value)}>
        <option value="">All</option>
        <option value="Easy">Easy</option>
        <option value="Medium">Medium</option>
        <option value="Hard">Hard</option>
      </select>

      <button onClick={search}>Search</button>

      <br /><br />

      <input type="file" onChange={(e) => setImage(e.target.files[0])} />
      <button onClick={upload}>Upload</button>

      {recipes.map((r, i) => (
        <div key={i} style={{ border: "1px solid gray", margin: 10, padding: 10 }}>
          <h3>{r.recipe}</h3>
          <p><b>Similarity:</b> {r.similarity}%</p>
          <p><b>Veg:</b> {r.veg}</p>
          <p><b>Time:</b> {r.time}</p>
          <p><b>Difficulty:</b> {r.difficulty}</p>

          <p><b>Nutrients:</b> {JSON.stringify(r.nutrients)}</p>

          <p><b>Ingredients:</b></p>
          <ul>
            {Array.isArray(r.ingredients) && r.ingredients.map((ing, idx) => (
              <li key={idx}>{ing}</li>
            ))}
          </ul>

          <p><b>Steps:</b></p>
          <ol>
            {Array.isArray(r.steps) && r.steps.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </div>
      ))}
    </div>
  );
}

export default App;
