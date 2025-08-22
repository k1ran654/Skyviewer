import { useState } from "react";

function App() {
  const [ign, setIgn] = useState("");
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  async function fetchProfile() {
    setError("");
    setProfile(null);

    try {
      // 1️⃣ Get UUID
      const uuidRes = await fetch(`http://localhost:3001/api/uuid/${ign}`);
      if (!uuidRes.ok) throw new Error("Player not found");
      const uuidData = await uuidRes.json();
      const uuid = uuidData.id;

      // 2️⃣ Get SkyBlock data
      const sbRes = await fetch(`http://localhost:3001/api/skyblock/${uuid}`);
      if (!sbRes.ok) throw new Error("No SkyBlock profiles found");
      const sbData = await sbRes.json();

      if (!sbData.profiles || sbData.profiles.length === 0) {
        throw new Error("No SkyBlock profiles found");
      }

      const latest = sbData.profiles.reduce((a, b) =>
        a.members[uuid].last_save > b.members[uuid].last_save ? a : b
      );

      const member = latest.members[uuid];

      setProfile({
        name: uuidData.name,
        profileName: latest.cute_name || "Unnamed",
        coinPurse: member.coin_purse || 0,
        skills: member.skills || {},
        minions: member.minions || {},
        pets: member.pets || {}
      });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>SkyViewer Lite</h1>
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
          <p>Purse: {Math.floor(profile.coinPurse).toLocaleString()} coins</p>

          <h3>Skills</h3>
          <ul>
            {Object.entries(profile.skills).map(([skill, level]) => (
              <li key={skill}>
                {skill}: {level}
              </li>
            ))}
          </ul>

          <h3>Minions</h3>
          <ul>
            {Object.entries(profile.minions).map(([minion, data]) => (
              <li key={minion}>
                {minion} — Level {data.level}, XP: {data.xp}
              </li>
            ))}
          </ul>

          <h3>Pets</h3>
          <ul>
            {Object.entries(profile.pets).map(([pet, data], index) => (
              <li key={index}>
                {pet} — Level {data.level || 1}, Rarity: {data.rarity || "Unknown"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
