/* ==============================================================================
   js/strategic-china.js — China Strategic Reference Layer (Phase 1 + Phase 2)
   ==============================================================================
   Self-contained module: owns its own data fetch, its own Leaflet layer, and
   its own on-map UI (panel with tier toggle, category filters, search, and
   an Exit control). index.html only has to:
     1. include this script (after Leaflet + Leaflet.markercluster + countries.js)
     2. call StrategicChina.init(map, baseTileLayer) once, after the main map exists
     3. call StrategicChina.activate(context) from the China country popup's
        button, where context = { riskLabel, riskValue, eventsCount, notesCount }
        — read-only display values computed by index.html from the EXISTING
        DATA/NOTES globals. This module never reads or writes event/risk data
        itself, and nothing here ever feeds back into it.

   Static public-source reference data — NOT real-time. See
   data/reference/china.geojson for the dataset and its fixed schema.
   ============================================================================== */

(function () {
  "use strict";

  const DATA_URL = "data/reference/china.geojson";

  // Rough bounding box around mainland China + Hainan, enough padding to keep
  // Zhanjiang/Hainan/Nanjing/Beijing all comfortably in frame.
  const CHINA_BOUNDS = [[17, 95], [54, 135]];
  const CHINA_CENTER = L.latLngBounds(CHINA_BOUNDS).getCenter();

  // The map's #map container is short (380px, 280px on mobile), so fitting
  // the full china bounds vertically collapses to barely more than the
  // global zoom (measured in Phase 1: zoom 3). flyTo a fixed regional zoom
  // instead — predictable regardless of container size, and still well
  // under the raised REGIONAL_MAX_ZOOM cap so users can zoom in further.
  const REGIONAL_START_ZOOM = 5;

  // Global default view (must match index.html's initMap() setView call) —
  // this is what "return to normal global view" resets back to on exit.
  const GLOBAL_VIEW = { center: [25, 30], zoom: 2 };

  const REGIONAL_MAX_ZOOM = 9;
  const GLOBAL_MAX_ZOOM = 8; // matches the tileLayer's maxZoom in index.html

  // Joseph Wen's public PLA-sites reference map — research inspiration only,
  // never embedded/depended on at runtime. Used for two things: (1) an
  // attribution line in the panel footer, (2) a per-feature "view this area"
  // link built from OUR OWN coordinates (never a specific pin of his).
  const WEN_MAP_URL = "https://www.google.com/maps/d/u/0/viewer?mid=19Q8BraU1Nmnk23TzMb5rhXFuIAnOpTTq";

  // Per-category marker styling. "ground" and "political-military" are part
  // of the documented category enum even though the current dataset has no
  // entries in either yet (see CATEGORY_GROUPS below, which still exposes a
  // filter checkbox for every group regardless of whether it currently
  // matches anything).
  const CATEGORY_STYLE = {
    "central-command":           { color: "#C9A44C", glyph: "C", label: "Central command" },
    "political-military":        { color: "#D18FBF", glyph: "P", label: "Political-military" },
    "navy":                      { color: "#3E7CB8", glyph: "N", label: "Navy" },
    "air":                       { color: "#4FB8C9", glyph: "A", label: "Air force" },
    "ground":                    { color: "#8A9A5B", glyph: "G", label: "Ground force" },
    "rocket":                    { color: "#D65A5A", glyph: "R", label: "Rocket force" },
    "joint-command":             { color: "#9B6FD1", glyph: "J", label: "Joint theater command" },
    "information-intelligence":  { color: "#55A97A", glyph: "I", label: "Information / intelligence" },
  };
  const DEFAULT_STYLE = { color: "#7E8FA0", glyph: "?", label: "Other / unclassified category" };

  function styleFor(category) {
    return CATEGORY_STYLE[category] || DEFAULT_STYLE;
  }

  // Category filter checkboxes shown in the panel. The spec's checkbox list
  // ("Navy · Air · Ground · Rocket · Joint/Command · Information/Intelligence
  // · Central/Political-Military") has 7 labels but the category enum has 8
  // values — the last checkbox is a deliberate COMBINED filter covering both
  // "central-command" and "political-military" as one group (confirmed by
  // the context-summary spec, which likewise shows a single combined
  // "Central XX" count, not a separate Political-Military count). See
  // NEEDS MY REVIEW in the chat response if a split into two checkboxes is
  // preferred instead.
  const CATEGORY_GROUPS = [
    { key: "navy",                     label: "Navy",                     values: ["navy"] },
    { key: "air",                      label: "Air",                      values: ["air"] },
    { key: "ground",                   label: "Ground",                   values: ["ground"] },
    { key: "rocket",                   label: "Rocket",                   values: ["rocket"] },
    { key: "joint-command",            label: "Joint/Command",            values: ["joint-command"] },
    { key: "information-intelligence", label: "Information/Intelligence", values: ["information-intelligence"] },
    { key: "central-political",        label: "Central/Political-Military", values: ["central-command", "political-military"] },
  ];
  function groupForCategory(cat) {
    return CATEGORY_GROUPS.find(g => g.values.indexOf(cat) !== -1) || null;
  }

  // Same escaping/validation discipline as index.html's esc()/safeUrl() —
  // source-derived AND user-typed (search) strings never go into innerHTML
  // unescaped, and only http(s) links are ever rendered as <a>.
  const esc = s => String(s).replace(/[&<>"]/g, ch =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
  const safeUrl = u => /^https?:\/\//i.test(String(u || "")) ? u : null;

  let map = null;
  let baseTileLayer = null;
  let clusterLayer = null;     // this layer's OWN markerClusterGroup — separate from event/country/lane layers
  let panelControl = null;
  let panelBodyEl = null;      // the part of the panel we rewrite in place (avoids losing search-box focus)
  let allEntries = [];         // [{ feature, marker }] built once, after the first successful fetch
  let cachedGeojson = null;    // set once fetched successfully; never refetched after
  let fetchFailed = false;
  let active = false;
  let chinaContext = null;     // { riskLabel, riskValue, eventsCount, notesCount } — read-only, passed in at activate()

  const filterState = {
    tier: "major",                                   // "major" | "all" — Major Sites is the default
    categories: new Set(CATEGORY_GROUPS.map(g => g.key)), // all filter groups on by default
    query: ""
  };

  /* ------------------------------------------------------------------------
     Marker + popup construction
     ---------------------------------------------------------------------- */
  function svgIcon(category) {
    const s = styleFor(category);
    const html = `<div class="strategic-marker" style="background:${s.color}">${s.glyph}</div>`;
    return L.divIcon({ className: "strategic-marker-wrap", html, iconSize: [22, 22], iconAnchor: [11, 11], popupAnchor: [0, -10] });
  }

  function broadLocationText(props, lat, lon) {
    const country = props.country || "—";
    if (typeof lat !== "number" || typeof lon !== "number") return country;
    return `${country} · ${Math.abs(lat).toFixed(2)}°${lat >= 0 ? "N" : "S"}, ${Math.abs(lon).toFixed(2)}°${lon >= 0 ? "E" : "W"}`;
  }

  function verificationLabel(status) {
    if (status === "verified") return "Verified";
    if (status === "source-reported") return "Source-reported (single public source)";
    return esc(status || "Unverified");
  }

  function popupHtml(props, lat, lon) {
    const name = esc(props.name || "Unnamed site");
    const branch = esc(props.branch || "—");
    const style = styleFor(props.category);
    const categoryLabel = esc(style.label);
    const broadLocation = esc(broadLocationText(props, lat, lon));
    const desc = esc(props.short_description || "No description available.");
    const lastReviewed = esc(props.last_reviewed || "—");

    const url = safeUrl(props.source_url);
    const sourceLabel = esc(props.source_label || "Source");
    const sourceHtml = url
      ? `<a href="${esc(url)}" target="_blank" rel="noopener">${sourceLabel}</a>`
      : `${sourceLabel} <span class="strategic-nolink">(no valid source link)</span>`;

    // "View area on Wen's map" — built from THIS feature's own coordinates,
    // never a specific pin of his. Validated with the same safeUrl() helper
    // as every other link, even though we constructed it ourselves.
    const wenAreaUrl = (typeof lat === "number" && typeof lon === "number")
      ? safeUrl(`${WEN_MAP_URL}&ll=${lat},${lon}&z=11`)
      : null;
    const wenHtml = wenAreaUrl
      ? `<div class="strategic-popup-wen"><a href="${esc(wenAreaUrl)}" target="_blank" rel="noopener noreferrer">View area on Wen's map ↗</a></div>`
      : "";

    const isTheaterLevel = /theater[\s-]level/i.test(props.short_description || "");
    const theaterHtml = isTheaterLevel
      ? `<div class="strategic-popup-theater">Approximate theater-level area — represents a broad zone of responsibility, not a precise facility location.</div>`
      : "";

    return `<div class="strategic-popup">
        <div class="strategic-popup-head">
          <span class="strategic-swatch" style="background:${style.color}">${esc(style.glyph)}</span>
          <span class="strategic-popup-title">${name}</span>
        </div>
        <div class="strategic-popup-meta">${branch} · ${categoryLabel}</div>
        <div class="strategic-popup-loc">${broadLocation}</div>
        <p class="strategic-popup-desc">${desc}</p>
        ${theaterHtml}
        <div class="strategic-popup-src">Source: ${sourceHtml}</div>
        ${wenHtml}
        <div class="strategic-popup-flag">Static public-source reference — not real-time</div>
        <div class="strategic-popup-verify">${verificationLabel(props.verification_status)} · last reviewed ${lastReviewed}</div>
      </div>`;
  }

  function buildEntries(geojson) {
    const entries = [];
    (geojson.features || []).forEach(feature => {
      try {
        const geom = feature.geometry;
        if (!geom || geom.type !== "Point" || !Array.isArray(geom.coordinates)) return;
        const [lon, lat] = geom.coordinates;
        const props = feature.properties || {};
        const marker = L.marker([lat, lon], { icon: svgIcon(props.category) });
        marker.bindPopup(popupHtml(props, lat, lon), { maxWidth: 280, className: "strategic-popup-wrap" });
        const searchText = [props.name, props.branch, styleFor(props.category).label, broadLocationText(props, lat, lon)]
          .filter(Boolean).join(" ").toLowerCase();
        entries.push({ feature, marker, lat, lon, searchText });
      } catch (err) {
        // One malformed feature never takes down the whole layer.
        console.warn("strategic-china: skipped a malformed feature", err, feature);
      }
    });
    return entries;
  }

  async function ensureData() {
    if (cachedGeojson || fetchFailed) return; // lazy-load once; cache after, don't retry a known failure
    try {
      const res = await fetch(DATA_URL, { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const j = await res.json();
      if (!j || !Array.isArray(j.features)) throw new Error("Unexpected GeoJSON shape");
      cachedGeojson = j;
      allEntries = buildEntries(cachedGeojson);
    } catch (err) {
      console.warn("strategic-china: could not load " + DATA_URL + " — layer unavailable.", err);
      fetchFailed = true;
    }
  }

  /* ------------------------------------------------------------------------
     Filtering, map sync, and the live context summary
     ---------------------------------------------------------------------- */
  function entryMatchesFilters(entry) {
    const props = entry.feature.properties || {};
    if (filterState.tier === "major" && props.importance !== "major") return false;
    const group = groupForCategory(props.category);
    // A category with no matching checkbox group (shouldn't happen given the
    // fixed schema, but the dataset isn't assumed infallible) is always
    // shown rather than silently hidden by a filter with no visible control.
    if (group && !filterState.categories.has(group.key)) return false;
    return true;
  }

  function visibleEntries() {
    return allEntries.filter(entryMatchesFilters);
  }

  function syncMapMarkers() {
    if (!clusterLayer) return;
    clusterLayer.clearLayers();
    clusterLayer.addLayers(visibleEntries().map(e => e.marker));
  }

  function renderSummary(visible) {
    if (!panelBodyEl) return;
    const el = panelBodyEl.querySelector(".strategic-summary");
    if (!el) return;
    const counts = {};
    CATEGORY_GROUPS.forEach(g => { counts[g.key] = 0; });
    visible.forEach(entry => {
      const group = groupForCategory(entry.feature.properties.category);
      if (group) counts[group.key]++;
    });
    const breakdown = CATEGORY_GROUPS.map(g => `${g.label} ${counts[g.key]}`).join(" · ");

    const riskLine = chinaContext
      ? `Current risk: <span class="stat-strong">${esc(chinaContext.riskLabel != null ? chinaContext.riskLabel : "—")}</span>` +
        (chinaContext.riskValue != null ? ` (${esc(chinaContext.riskValue)}/10)` : "") +
        ` &nbsp;·&nbsp; Current events: <span class="stat-strong">${esc(chinaContext.eventsCount != null ? chinaContext.eventsCount : "—")}</span>`
      : `Current risk / events: not available`;
    const notesLine = chinaContext
      ? `Analyst notes: <span class="stat-strong">${esc(chinaContext.notesCount != null ? chinaContext.notesCount : "—")}</span>`
      : "";

    el.innerHTML = `
      <div>Curated reference locations: <span class="stat-strong">${visible.length}</span></div>
      <div class="strategic-summary-breakdown">${breakdown}</div>
      <hr>
      <div>${riskLine}</div>
      <div>${notesLine}</div>`;
  }

  function renderSearchResults() {
    if (!panelBodyEl) return;
    const resultsEl = panelBodyEl.querySelector(".strategic-search-results");
    if (!resultsEl) return;
    const q = filterState.query.trim().toLowerCase();
    if (!q) { resultsEl.innerHTML = ""; return; }

    const matches = visibleEntries().filter(e => e.searchText.indexOf(q) !== -1).slice(0, 8);
    if (!matches.length) {
      resultsEl.innerHTML = `<div class="strategic-search-empty">No matches for "${esc(filterState.query.trim())}".</div>`;
      return;
    }
    resultsEl.innerHTML = matches.map((entry, i) =>
      `<button type="button" class="strategic-search-result" data-idx="${i}">${esc(entry.feature.properties.name || "Unnamed site")}</button>`
    ).join("");
    resultsEl.querySelectorAll(".strategic-search-result").forEach((btn, i) => {
      btn.addEventListener("click", () => selectSearchResult(matches[i]));
    });
  }

  function selectSearchResult(entry) {
    if (!clusterLayer || !map) return;
    // zoomToShowLayer pans/zooms until the marker is out of any cluster,
    // then opens its popup — the correct Leaflet.markercluster idiom for
    // "jump to this specific feature," rather than a manual flyTo that
    // might still leave it spiderfied/clustered.
    clusterLayer.zoomToShowLayer(entry.marker, () => entry.marker.openPopup());
  }

  function refresh() {
    const visible = visibleEntries();
    syncMapMarkers();
    renderSummary(visible);
    renderSearchResults();
  }

  /* ------------------------------------------------------------------------
     On-map control
     ---------------------------------------------------------------------- */
  function interactivePanelBodyHtml() {
    const tierRow = `
      <div class="strategic-tier-toggle" role="radiogroup" aria-label="Site tier">
        <label><input type="radio" name="strategic-tier" value="major" ${filterState.tier === "major" ? "checked" : ""}> Major Sites</label>
        <label><input type="radio" name="strategic-tier" value="all" ${filterState.tier === "all" ? "checked" : ""}> All Curated Sites</label>
      </div>`;

    const filterRows = CATEGORY_GROUPS.map(g => {
      const swatches = g.values.map(v => `<span class="strategic-swatch small" style="background:${styleFor(v).color}">${esc(styleFor(v).glyph)}</span>`).join("");
      const checked = filterState.categories.has(g.key) ? "checked" : "";
      return `<label><input type="checkbox" class="strategic-cat-filter" data-key="${esc(g.key)}" ${checked}> <span class="swatch-pair">${swatches}</span> ${esc(g.label)}</label>`;
    }).join("");

    return `
      <div class="strategic-summary"></div>
      ${tierRow}
      <div class="strategic-filters">${filterRows}</div>
      <div class="strategic-search">
        <input type="text" placeholder="Search strategic sites" aria-label="Search strategic sites">
        <div class="strategic-search-results"></div>
      </div>`;
  }

  function wireInteractivePanel() {
    if (!panelBodyEl) return;

    panelBodyEl.querySelectorAll('input[name="strategic-tier"]').forEach(radio => {
      radio.addEventListener("change", ev => {
        filterState.tier = ev.target.value;
        refresh();
      });
    });
    panelBodyEl.querySelectorAll(".strategic-cat-filter").forEach(cb => {
      cb.addEventListener("change", ev => {
        const key = ev.target.dataset.key;
        if (ev.target.checked) filterState.categories.add(key); else filterState.categories.delete(key);
        refresh();
      });
    });
    const searchInput = panelBodyEl.querySelector('.strategic-search input[type="text"]');
    if (searchInput) {
      searchInput.addEventListener("input", ev => {
        filterState.query = ev.target.value;
        renderSearchResults();
      });
    }
  }

  const StrategicControl = L.Control.extend({
    options: { position: "topright" },
    onAdd: function () {
      const div = L.DomUtil.create("div", "strategic-panel");
      L.DomEvent.disableClickPropagation(div);
      L.DomEvent.disableScrollPropagation(div);

      const creditHtml = safeUrl(WEN_MAP_URL)
        ? `<div class="strategic-panel-credit">Reference: <a href="${esc(WEN_MAP_URL)}" target="_blank" rel="noopener noreferrer">Joseph Wen's PLA map ↗</a> — Evintir shows a curated, sourced subset; his public map documents thousands more sites.</div>`
        : "";

      div.innerHTML = `
        <div class="strategic-panel-title">China Strategic Reference</div>
        <div class="strategic-panel-flag">Static public-source reference — not real-time</div>
        <div class="strategic-panel-body"><div class="strategic-loading">Loading strategic reference data…</div></div>
        <button type="button" class="strategic-exit-btn">Exit Strategic View</button>
        ${creditHtml}`;

      div.querySelector(".strategic-exit-btn").addEventListener("click", deactivate);
      panelBodyEl = div.querySelector(".strategic-panel-body");
      return div;
    }
  });

  /* ------------------------------------------------------------------------
     Activate / deactivate
     ---------------------------------------------------------------------- */
  async function activate(context) {
    if (!map || active) return;
    active = true;
    chinaContext = context || null;

    map.closePopup(); // clear the China country popup this was launched from

    // Raise the zoom ceiling for regional exploration; restored on exit.
    map.setMaxZoom(REGIONAL_MAX_ZOOM);
    if (baseTileLayer) baseTileLayer.options.maxZoom = REGIONAL_MAX_ZOOM;

    map.flyTo(CHINA_CENTER, REGIONAL_START_ZOOM, { duration: 1.1 });

    // Reset filter/search state each time the view is (re-)opened.
    filterState.tier = "major";
    filterState.categories = new Set(CATEGORY_GROUPS.map(g => g.key));
    filterState.query = "";

    panelControl = new StrategicControl();
    panelControl.addTo(map);

    await ensureData();
    if (!panelControl || !panelBodyEl) return; // deactivated while loading

    if (fetchFailed) {
      panelBodyEl.innerHTML = `<div class="strategic-unavailable">Strategic reference data unavailable — could not load ${esc(DATA_URL)}. Rest of Evintir is unaffected.</div>`;
      return;
    }

    try {
      clusterLayer = clusterLayer || L.markerClusterGroup({
        maxClusterRadius: 34,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        iconCreateFunction: cluster => {
          const count = cluster.getChildCount();
          const size = count < 5 ? "small" : count < 12 ? "medium" : "large";
          return L.divIcon({
            html: `<div>${count}</div>`,
            className: `strategic-cluster strategic-cluster-${size}`,
            iconSize: L.point(34, 34)
          });
        }
      });
      map.addLayer(clusterLayer);

      panelBodyEl.innerHTML = interactivePanelBodyHtml();
      wireInteractivePanel();
      refresh();
    } catch (err) {
      // Layer construction failure is non-fatal too — same "unavailable" story.
      console.warn("strategic-china: layer setup failed, marking unavailable.", err);
      fetchFailed = true;
      panelBodyEl.innerHTML = `<div class="strategic-unavailable">Strategic reference layer failed to initialize. Rest of Evintir is unaffected.</div>`;
    }
  }

  function deactivate() {
    if (!active) return;
    active = false;

    if (clusterLayer && map.hasLayer(clusterLayer)) map.removeLayer(clusterLayer);
    if (panelControl) { map.removeControl(panelControl); panelControl = null; panelBodyEl = null; }

    // Cancel any pan/zoom still in flight (e.g. a search result's
    // zoomToShowLayer animation) and reset the view WHILE maxZoom is still
    // raised — dropping maxZoom first (while the current zoom is above the
    // new cap) makes Leaflet clamp-animate down on its own, which can race
    // the setView below and win, leaving the map stuck wherever the search
    // left it. Found via testing: exit right after a search-result select.
    map.stop();
    map.closePopup();
    map.setView(GLOBAL_VIEW.center, GLOBAL_VIEW.zoom, { animate: false });

    map.setMaxZoom(GLOBAL_MAX_ZOOM);
    if (baseTileLayer) baseTileLayer.options.maxZoom = GLOBAL_MAX_ZOOM;
  }

  function init(mapInstance, baseTileLayerInstance) {
    map = mapInstance;
    baseTileLayer = baseTileLayerInstance || null;
  }

  window.StrategicChina = {
    init,
    activate,
    deactivate,
    isActive: () => active,
    toggle: (context) => (active ? deactivate() : activate(context))
  };
})();
