# NOTICE — External Data & Asset Sources

Catalogues every external data source and licensed asset this project pulls
in, beyond what's already credited in README.md's Credits section (map
tiles, Leaflet, OpenStreetMap). Kept current as sources are added — this is
a licensing-compliance record, not a one-time task.

## Country emblem images (Wikimedia Commons)

Sourced via the `Special:FilePath/<File_Name>.svg` redirect (no MD5 hash
needed) and referenced in `countries.js`. Each is a national-level emblem;
the correct term is used per country (not defaulted to "coat of arms" —
e.g. Japan's is the Imperial Seal, not a heraldic coat of arms).

License status below is **spot-checked directly against the Commons file
page** for 6 of the 22 (marked ✅ verified this session, with the date). The
remaining 16 carry the license Commons states on their own file page, but
that specific claim was **not independently re-confirmed in this session**
— recommend a full pass before any reuse beyond this project's own
display-only usage (an `<img>` tag with source attribution, no
redistribution of the file itself).

| Country | File | License (per Commons) | Verified |
|---|---|---|---|
| United States | Coat_of_arms_of_the_United_States.svg | US gov't work (17 U.S.C. §105), PD | ✅ 2026-08-06 |
| Japan | Imperial_Seal_of_Japan.svg | PD-Japan (Copyright Act Art. 13) + PD-US (gov't edict) | ✅ 2026-08-06 |
| North Korea | Emblem_of_North_Korea.svg | PD-North-Korea-exempt + PD-1996 (URAA) | ✅ 2026-08-06 |
| China | National_Emblem_of_the_People's_Republic_of_China.svg | PD-PRC-exempt (official state document exemption) | ✅ 2026-08-06 |
| United Kingdom | Royal_Coat_of_Arms_of_the_United_Kingdom_(HM_Government)_(St_Edwards_Crown).svg | **CC BY-SA 3.0/2.5/2.0/1.0 + GFDL — NOT public domain, requires attribution** | ✅ 2026-08-06 |
| Iran | Emblem_of_Iran.svg | PD-Iran (expired term) / PD-ineligible (simple geometry) / CC0 | ✅ 2026-08-06 |
| Russia | Coat_of_Arms_of_the_Russian_Federation.svg | Per Commons file page | not re-verified |
| Ukraine | Lesser_Coat_of_Arms_of_Ukraine.svg | Per Commons file page | not re-verified |
| India | Emblem_of_India.svg | Per Commons file page | not re-verified |
| France | Emblem_of_the_French_Republic.svg | Per Commons file page | not re-verified |
| Germany | Coat_of_arms_of_Germany.svg | Per Commons file page | not re-verified |
| Israel | Emblem_of_Israel.svg | Per Commons file page | not re-verified |
| Pakistan | State_emblem_of_Pakistan.svg | Per Commons file page | not re-verified |
| South Korea | Emblem_of_South_Korea.svg | Per Commons file page | not re-verified |
| Indonesia | National_emblem_of_Indonesia_Garuda_Pancasila.svg | Per Commons file page | not re-verified |
| Australia | Coat_of_arms_of_the_Commonwealth_of_Australia.svg | Per Commons file page | not re-verified |
| Mexico | Coat_of_arms_of_Mexico.svg | Per Commons file page | not re-verified |
| Turkey | Emblem_of_Turkey.svg | Per Commons file page | not re-verified |
| Saudi Arabia | Emblem_of_Saudi_Arabia.svg | Per Commons file page | not re-verified |
| United Arab Emirates | Emblem_of_the_United_Arab_Emirates.svg | Per Commons file page | not re-verified |
| Qatar | Emblem_of_Qatar.svg | Per Commons file page | not re-verified |
| Kuwait | Emblem_of_Kuwait.svg | Per Commons file page | not re-verified |

**Action item surfaced by this spot-check:** the UK file is CC BY-SA/GFDL,
not public domain like the others — it legally requires attribution on
reuse. This project's use (an `<img>` on the page, sourced directly from
Commons via hotlink, with `alt="United Kingdom"`) is a reasonable-faith
reading of "attribution" for a personal/portfolio project, but a proper CC
BY-SA attribution line (author + license link) has not been added anywhere
on-page. Worth doing before treating this as fully compliant.

## RSS feed sources (`scripts/fetch_feeds.py` → `FEEDS`)

Headlines and links only are ingested — no full article text is stored,
scraped, or republished. Each event's `source_url` links back to the
original publisher.

| Source | Basis for use |
|---|---|
| CISA Advisories | U.S. government work — public domain (17 U.S.C. §105) |
| U.S. DoD Releases | U.S. government work — public domain (17 U.S.C. §105) |
| BBC World (RSS) | BBC publishes this feed for syndication; headline + link only, per BBC's own RSS terms |
| Al Jazeera (RSS) | Publisher-provided public RSS feed; headline + link only |
| gCaptain (maritime, RSS) | Publisher-provided public RSS feed; headline + link only |

## Planned, not yet integrated

- **Marine Regions EEZ boundaries** (Flanders Marine Institute / UNESCO) —
  citable DOI dataset, free GeoJSON/Shapefile. Not yet pulled into the repo.
- **Shipping lane reference corridors** —
  [newzealandpaul/Shipping-Lanes](https://github.com/newzealandpaul/Shipping-Lanes)
  (CC BY 4.0), georeferenced from a declassified CIA "Map of the World's
  Oceans" (2012). Requires attribution per CC BY 4.0 when integrated. Must
  be labeled as a static 2012 reference source — explicitly not live
  AIS/vessel-traffic data.

This section moves to the tables above once either dataset is actually
added to the repo.
