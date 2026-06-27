# Deezer Music Data Engineering Pipeline

A small end-to-end ETL (Extract → Transform → Load) pipeline that pulls top
chart data from the Deezer API, models it into a star-schema-style
fact/dimension structure, and loads it into a PostgreSQL data warehouse.

## Architecture

```
Deezer API
    │
    ▼
extract.py   ──► data/raw_data/ (songs / artists / albums JSON)
    │
    ▼
explore.py   ──► quick EDA on the raw chart JSON (console output only)
    │
    ▼
transform.py ──► data/processed_data/ (fact_tracks.csv, dim_artists.csv, dim_albums.csv)
    │
    ▼
load.py      ──► PostgreSQL (fact_tracks, dim_artists, dim_albums tables)
```

**Data model (star schema):**
- `dim_artists` — artist_id (PK), artist_name, nb_album, nb_fan
- `dim_albums` — album_id (PK), album_title, release_date, genre_id
- `fact_tracks` — track_id (PK), artist_id (FK), album_id (FK), title, duration, rank, explicit_lyrics, load_timestamp

## Tech stack

- Python 3
- `requests` — Deezer API calls
- `pandas` — data wrangling / CSV staging
- `psycopg2` — PostgreSQL driver
- `python-dotenv` — environment variable / secrets management
- PostgreSQL + pgAdmin — data warehouse

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   ```

2. Install dependencies:
   ```bash
   pip install requests pandas psycopg2-binary python-dotenv
   ```

3. Create a PostgreSQL database (e.g. via pgAdmin) named `deezer_dw`.

4. Copy `.env.example` to `.env` and fill in your real credentials:
   ```bash
   cp .env.example .env
   ```

## Running the pipeline

Run each stage in order:

```bash
python extract.py     # pulls chart + artist + album data from Deezer
python explore.py      # optional: quick look at the raw data
python transform.py    # builds fact/dimension CSVs
python load.py          # loads CSVs into PostgreSQL (upsert, idempotent)
```

Re-running `extract.py` is safe — it skips artists/albums already
downloaded. Re-running `load.py` is also safe — it upserts rather than
duplicating rows.

## Resetting / starting fresh

To wipe generated data and start over:

```bash
rm -rf data/raw_data data/processed_data logs   # Mac/Linux
rmdir /s /q data\raw_data data\processed_data logs   # Windows
```

## Notes

- All credentials are loaded from a local `.env` file (never committed —
  see `.gitignore`). Use `.env.example` as a template.
- Logs for every run are written to `logs/pipeline.log`. 