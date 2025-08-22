require('dotenv').config();
const express = require("express");
const fetch = require("node-fetch");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 3001;  // Use Render's assigned port or fallback

app.use(cors());

app.get("/api/uuid/:ign", async (req, res) => {
  try {
    const ign = req.params.ign;
    const response = await fetch(`https://api.mojang.com/users/profiles/minecraft/${ign}`);
    if (!response.ok) return res.status(404).json({ error: "Player not found" });
    const data = await response.json();
    res.json(data);
  } catch {
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/api/skyblock/:uuid", async (req, res) => {
  const uuid = req.params.uuid;

  try {
    const response = await fetch(`https://api.hypixel.net/skyblock/profiles?uuid=${uuid}`, {
      headers: {
        'API-Key': process.env.HYPIXEL_API_KEY
      }
    });

    if (!response.ok) {
      return res.status(response.status).json({ error: "Failed to fetch SkyBlock profiles" });
    }

    const data = await response.json();

    if (!data || !data.profiles || data.profiles.length === 0) {
      return res.status(404).json({ error: "No SkyBlock profiles found" });
    }

    res.json(data);
  } catch (err) {
    console.error("🔥 Backend error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
