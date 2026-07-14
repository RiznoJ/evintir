/* ==========================================================================
   countries.js — SHARED country lookup table + small helpers.
   ==========================================================================
   This file is the SINGLE SOURCE OF TRUTH for country metadata. Both
   index.html (the map) and analyst.html (the notes feed) include it with
   <script src="countries.js"></script>, so there is exactly one copy to keep
   correct — do NOT paste a second copy into either HTML file.

   It's a plain (classic) script, not a module: the top-level `const COUNTRIES`
   and the helper functions land in the page's global scope, so the inline
   <script> further down each page can use them directly.

   `country` fields inside data/notes.json MUST match a key here exactly
   ("Russia", not "Russian Federation"; "United States", not "USA").
   ========================================================================== */

const COUNTRIES = {
  "United States":  { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Coat_of_arms_of_the_United_States.svg", lat: 39.8, lon: -98.6, matchRegion: "United States" },
  "Russia":         { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Coat_of_Arms_of_the_Russian_Federation.svg", lat: 61.5, lon: 105.3, matchRegion: "Europe / Russia-Ukraine" },
  "Ukraine":        { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Lesser_Coat_of_Arms_of_Ukraine.svg", lat: 48.4, lon: 31.2, matchRegion: "Europe / Russia-Ukraine" },
  "China":          { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:National_Emblem_of_the_People's_Republic_of_China.svg", lat: 35.9, lon: 104.2, matchRegion: "Global" },
  "India":          { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_India.svg", lat: 22.0, lon: 79.0, matchRegion: "Global" },
  "United Kingdom": { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Royal_Coat_of_Arms_of_the_United_Kingdom.svg", lat: 55.4, lon: -3.4, matchRegion: "Global" },
  "France":         { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_the_French_Republic.svg", lat: 46.6, lon: 2.2, matchRegion: "Global" },
  "Germany":        { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Coat_of_arms_of_Germany.svg", lat: 51.2, lon: 10.4, matchRegion: "Global" },
  "Israel":         { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_Israel.svg", lat: 31.0, lon: 34.8, matchRegion: "Middle East" },
  "Iran":           { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_Iran.svg", lat: 32.4, lon: 53.7, matchRegion: "Middle East" },
  "Pakistan":       { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:State_emblem_of_Pakistan.svg", lat: 30.4, lon: 69.3, matchRegion: "Global" },
  "Japan":          { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Imperial_Seal_of_Japan.svg", lat: 36.2, lon: 138.3, matchRegion: "Global" },
  "South Korea":    { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_South_Korea.svg", lat: 35.9, lon: 127.8, matchRegion: "Global" },
  "North Korea":    { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_North_Korea.svg", lat: 40.3, lon: 127.5, matchRegion: "Global" },
  "Indonesia":      { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:National_emblem_of_Indonesia_Garuda_Pancasila.svg", lat: -2.5, lon: 118.0, matchRegion: "Global" },
  "Australia":      { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Coat_of_arms_of_the_Commonwealth_of_Australia.svg", lat: -25.3, lon: 133.8, matchRegion: "Global" },
  "Mexico":         { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Coat_of_arms_of_Mexico.svg", lat: 23.6, lon: -102.5, matchRegion: "Global" },
  "Turkey":         { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_Turkey.svg", lat: 38.9, lon: 35.2, matchRegion: "Middle East" },
  "Saudi Arabia":   { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_Saudi_Arabia.svg", lat: 23.9, lon: 45.1, matchRegion: "Middle East" },
  "United Arab Emirates": { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_the_United_Arab_Emirates.svg", lat: 23.4, lon: 53.8, matchRegion: "Middle East" },
  "Qatar":          { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_Qatar.svg", lat: 25.3, lon: 51.2, matchRegion: "Middle East" },
  "Kuwait":         { coatOfArms: "https://commons.wikimedia.org/wiki/Special:FilePath/File:Emblem_of_Kuwait.svg", lat: 29.3, lon: 47.5, matchRegion: "Middle East" }
};
// NOTE: matchRegion is approximate. events.json only tags broad regions
// today ("Middle East" | "Global" | "United States" | "Europe /
// Russia-Ukraine"), not individual countries. Most non-Middle-East,
// non-Russia/Ukraine, non-US countries fall back to "Global" — so the map's
// "News" tab for, say, Japan or Australia is really "recent Global-tagged
// events," NOT a Japan- or Australia-specific news feed. This is a known
// limitation, not a bug; don't read it as country-level reporting.

/* --------------------------------------------------------------------------
   Shared helpers (used by both pages so colors/labels stay identical).
   -------------------------------------------------------------------------- */

// Risk band for a country RING, keyed off the highest risk_score among the
// events that matched its region. Hex values mirror index.html's riskBand()
// on purpose so a country ring and an event dot at the same risk read alike.
// A null score (country has posts but zero matched events) => neutral grey,
// which honestly signals "no risk data" rather than implying "low risk."
function countryBand(maxRisk) {
  if (maxRisk == null)  return { cls: "none", color: "#7E8FA0", label: "NO EVENT DATA" }; // --muted
  if (maxRisk >= 7)     return { cls: "high", color: "#D65A5A", label: "HIGH" };
  if (maxRisk >= 4)     return { cls: "med",  color: "#E0A93E", label: "ELEVATED" };
  return                       { cls: "low",  color: "#55A97A", label: "GUARDED" };
}

// Highest risk_score among events whose region == this country's matchRegion.
// Returns null when the country matches no events in the feed.
function countryMaxRisk(name, events) {
  const c = COUNTRIES[name];
  if (!c || !Array.isArray(events)) return null;
  const scores = events.filter(e => e.region === c.matchRegion).map(e => e.risk_score);
  return scores.length ? Math.max(...scores) : null;
}

// Two-letter fallback shown inside a badge when its coat-of-arms image fails
// to load (e.g. offline, or Wikimedia hotlink blocked). "United States" -> US,
// "Iran" -> IR.
function countryInitials(name) {
  const words = String(name).trim().split(/\s+/);
  const letters = words.length >= 2
    ? words[0][0] + words[1][0]
    : words[0].slice(0, 2);
  return letters.toUpperCase();
}

// Distinct country names that actually have at least one post, in table order
// (so badges don't jump around). Countries not present in COUNTRIES are
// dropped with a console warning — that means a notes.json `country` value
// didn't match a table key exactly.
function activeCountries(posts) {
  const present = new Set((posts || []).map(p => p.country));
  present.forEach(name => {
    if (name && !COUNTRIES[name]) {
      console.warn(`notes.json country "${name}" has no match in COUNTRIES — badge skipped.`);
    }
  });
  return Object.keys(COUNTRIES).filter(name => present.has(name));
}
