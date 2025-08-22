import { useState } from "react";

function App() {
  const [ign, setIgn] = useState("");
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  async function fetchProfile() {
    setError("");
    setProfile(null);

    try {
      // Step 1: Get UUID from backend
      const uuidRes = await fetch(`http://localhost:3001/api/uuid/${ign}`);
      if (!uuidRes.ok) throw new Error("Player not found");
      const uuidData = await uuidRes.json();
      const uuid = uuidData.id;

      // Step 2: Get SkyBlock profiles from backend
      const sbRes = await fetch(`http://localhost:3001/api/skyblock/${uuid}`);
      if (!sbRes.ok) throw new Error("No SkyBlock profiles found");
      const sbData = await sbRes.json();

      if (!sbData.profiles || sbData.profiles.length === 0) {
        throw new Error("No SkyBlock profiles found");
      }

      // Get the most recently played profile
      const latest = sbData.profiles.reduce((a, b) =>
        a.members[uuid].last_save > b.members[uuid].last_save ? a : b
      );

      const purse = latest.members[uuid].coin_purse || 0;
      const profileName = latest.cute_name || "Unnamed";

      setProfile({
        name: uuidData.name,
        purse,
        profileName
      });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>SkyCrypt Lite</h1>
      <input
        type="text"
        value={ign}
        onChange={(e) => setIgn(e.target.value)}
        placeholder="Enter Minecraft IGN"
      />
      <button onClick={fetchProfile}>View Profile</button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {profile && (
        <div>
          <h2>{profile.name}</h2>
          <p>Profile: {profile.profileName}</p>
          <p>Purse: {Math.floor(profile.purse).toLocaleString()} coins</p>
        </div>
      )}
    </div>
  );
}

export default App;