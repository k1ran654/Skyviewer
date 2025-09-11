require('dotenv').config({ path: './api.env' }); // load HYPIXEL_API_KEY
const express = require("express");
const fetch = require("node-fetch");
const cors = require("cors");
const path = require("path");
app.use(express.static(path.join(__dirname, "frontend", "dist")));

app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "frontend", "dist", "index.html"));
});

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());

// --- your existing API code unchanged ---

// Normalize UUID
function normalizeUUID(uuid) {
  return uuid.replace(/-/g, '');
}

// Cache
const cache = new Map();
const UUID_CACHE_TIME = 24 * 60 * 60 * 1000; // 24h
const PROFILE_CACHE_TIME = 3 * 60 * 1000;    // 3 min

// Get UUID from Mojang
app.get("/api/uuid/:ign", async (req, res) => {
  try {
    const ign = req.params.ign;

    if (cache.has(ign)) {
      const cached = cache.get(ign);
      if (Date.now() - cached.timestamp < UUID_CACHE_TIME) {
        return res.json(cached.data);
      }
    }

    const response = await fetch(`https://api.mojang.com/users/profiles/minecraft/${ign}`);
    if (!response.ok) return res.status(404).json({ error: "Player not found" });

    const data = await response.json();
    cache.set(ign, { data, timestamp: Date.now() });
    res.json(data);
  } catch (err) {
    console.error("🔥 Error fetching UUID:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

// Get SkyBlock profile from Hypixel
app.get("/api/skyblock/:uuid", async (req, res) => {
  try {
    const rawUUID = normalizeUUID(req.params.uuid);

    if (cache.has(rawUUID)) {
      const cached = cache.get(rawUUID);
      if (Date.now() - cached.timestamp < PROFILE_CACHE_TIME) {
        return res.json(cached.data);
      }
    }

    if (!process.env.HYPIXEL_API_KEY) {
      return res.status(500).json({ error: "Hypixel API key is missing" });
    }

    const response = await fetch(
      `https://api.hypixel.net/player?uuid=${rawUUID}&key=${process.env.HYPIXEL_API_KEY}`
    );
    if (!response.ok) return res.status(response.status).json({ error: "Failed to fetch player data" });

    const playerData = await response.json();
    if (!playerData.success || !playerData.player) {
      return res.status(404).json({ error: "Player not found or has never joined Hypixel" });
    }

    const skyblock = playerData.player.stats?.SkyBlock || {};

    const profile = {
      profiles: [
        {
          cute_name: "Main Profile",
          members: {
            [rawUUID]: {
              coin_purse: skyblock.coin_purse || 0,
              skills: skyblock.skills || {},
              minions: skyblock.minions || {},
              pets: skyblock.pets || {}
            }
          }
        }
      ]
    };

    cache.set(rawUUID, { data: profile, timestamp: Date.now() });
    res.json(profile);
  } catch (err) {
    console.error("🔥 Backend error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

// --- NEW: serve frontend ---
app.use(express.static(path.join(__dirname, "dist")));

app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "dist", "index.html"));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Server running on port ${PORT}`);
});
