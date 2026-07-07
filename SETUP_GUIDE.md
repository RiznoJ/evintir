# Setup Guide — from zero to a live dashboard (~30 minutes)

Follow this top to bottom. Every step says what you're doing AND why.
No prior GitHub experience assumed. Do these steps yourself — the account
and commits must be yours.

## Vocabulary (60 seconds)

- **Repository (repo):** a project folder that GitHub tracks. Yours will be public.
- **Commit:** a saved snapshot of the project with a message. Your commit
  history is the story of your work — it's evidence.
- **GitHub Pages:** free hosting that turns your repo into a live website.
- **GitHub Actions:** free robots that run scripts on a schedule. Ours
  refreshes the news data every 6 hours.

## Step 1 — Create your GitHub account (5 min)

1. Go to github.com → Sign up.
2. Username: professional (it goes on your resume). FirstnameLastname works.
3. Verify your email.

## Step 2 — Create the repository (3 min)

1. Click the **+** (top right) → **New repository**.
2. Name: `watchstander` (or your own name for it — lowercase, no spaces).
3. Description: "Public-source strategic monitoring dashboard — personal
   learning & portfolio project."
4. Select **Public**. Do NOT check "Add a README" (we have one).
5. Click **Create repository**.

## Step 3 — Upload the project (5 min)

Web upload first (git command line comes later, as a lesson):

1. On your new empty repo page, click **uploading an existing file**.
2. Unzip the project on your computer. Drag ALL contents of the folder in —
   including `data`, `scripts`, and `docs` folders.
   ⚠️ The `.github` folder is hidden on most computers and often does NOT
   drag in. Check after uploading: if you don't see `.github/workflows/`
   in the repo, add it by hand: **Add file → Create new file**, type
   `.github/workflows/update-feeds.yml` as the filename (the slashes create
   the folders), paste the file's contents in, and commit.
3. Commit message: `Initial commit: v2 dashboard, data pipeline, docs`
4. Click **Commit changes**.

## Step 4 — Turn on GitHub Pages (2 min)

1. In the repo: **Settings → Pages** (left sidebar).
2. Under "Build and deployment": Source = **Deploy from a branch**,
   Branch = **main**, folder = **/ (root)**. Save.
3. Wait 1–2 minutes. Your live URL appears at the top:
   `https://YOURNAME.github.io/watchstander/`
4. Open it. You should see the dashboard with the sample events on the map.

## Step 5 — Turn on the data robot (3 min)

1. In the repo: **Actions** tab. If prompted, click
   **I understand my workflows, enable them**.
2. Click **Update event feeds** (left) → **Run workflow** → Run.
3. Wait ~1 minute, refresh. Green check = it worked: the robot fetched real
   public news and committed a new `data/events.json`.
4. Refresh your live site — real headlines now populate the feed and map.
   From now on it refreshes itself every 6 hours.

If the run fails (red X): click into it, read the log, and bring the error
message to Claude/Opus. Reading error logs IS the lesson.

## Step 6 — Verify your safety rails (2 min)

- Repo contains `.gitignore` with `.env` listed → real secrets can never be
  committed by accident.
- `.env.example` has placeholders only.
- Confirm no file in the repo contains a password or key. (v2 uses none.)

## Step 7 — Run it on your own computer (10 min, optional today)

1. Install Python from python.org (check "Add to PATH" during install).
2. Download your repo: green **Code** button → **Download ZIP** → unzip.
3. Open a terminal in that folder and run:
   ```
   python -m http.server
   ```
   (This starts a tiny local web server — needed because browsers block
   data loading from double-clicked files, a security rule called CORS.)
4. Open http://localhost:8000 in your browser. Ctrl+C in the terminal stops it.

## What to ask Opus later (cheap questions, good lessons)

- "Walk me through what each line of the workflow YAML does."
- "Explain fetch() and why CORS blocked my double-clicked file."
- "Help me install git and make my next commit from the command line
  instead of the web uploader."
- "Review my 'What I learned' README section for accuracy."
