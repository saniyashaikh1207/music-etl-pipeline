# 4. load.py

import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "deezer_dw"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD")
}


class DeezerLoader:

    def __init__(self):
        self.processed_data_path = "data/processed_data"
        self.conn = None
        self.cursor = None


    def connect(self):

        if not DB_CONFIG["password"]:
            logging.critical(
                "DB_PASSWORD not found. Make sure a .env file exists with "
                "DB_PASSWORD set, and that python-dotenv is installed."
            )
            raise ValueError("Missing DB_PASSWORD environment variable.")
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            logging.info("Connected to PostgreSQL successfully.")
        except Exception as e:
            logging.critical(f"Failed to connect to PostgreSQL: {e}")
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logging.info("PostgreSQL connection closed.")

  
    def create_tables(self):
        create_dim_artists = """
        CREATE TABLE IF NOT EXISTS dim_artists (
            artist_id   BIGINT PRIMARY KEY,
            artist_name TEXT,
            nb_album    INTEGER,
            nb_fan      INTEGER
        );
        """

        create_dim_albums = """
        CREATE TABLE IF NOT EXISTS dim_albums (
            album_id     BIGINT PRIMARY KEY,
            album_title  TEXT,
            release_date DATE,
            genre_id     BIGINT
        );
        """
        create_fact_tracks = """
        CREATE TABLE IF NOT EXISTS fact_tracks (
            track_id        BIGINT PRIMARY KEY,
            artist_id       BIGINT REFERENCES dim_artists(artist_id),
            album_id        BIGINT REFERENCES dim_albums(album_id),
            title           TEXT,
            duration        INTEGER,
            rank            INTEGER,
            explicit_lyrics BOOLEAN,
            load_timestamp  TIMESTAMP DEFAULT NOW()
        );
        """

        for ddl in (create_dim_artists, create_dim_albums, create_fact_tracks):
            self.cursor.execute(ddl)

        self.conn.commit()
        logging.info("Tables verified/created: dim_artists, dim_albums, fact_tracks.")

    def upsert_dataframe(self, df, table_name, pk_column):
        if df.empty:
            logging.warning(f"No rows to load for {table_name}, skipping.")
            return

        columns = list(df.columns)
        update_columns = [c for c in columns if c != pk_column]
        update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])

        clean_df = df.astype(object).where(pd.notnull(df), None)
        values = [tuple(row) for row in clean_df.values.tolist()]

        insert_query = f"""
            INSERT INTO {table_name} ({", ".join(columns)})
            VALUES %s
            ON CONFLICT ({pk_column})
            DO UPDATE SET {update_clause};
        """

        try:
            execute_values(self.cursor, insert_query, values)
            self.conn.commit()
            logging.info(f"Upserted {len(values)} rows into {table_name}.")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Upsert failed for {table_name}: {e}")
            logging.error(f"Column dtypes:\n{df.dtypes}")
            logging.error(f"First 5 rows being inserted:\n{values[:5]}")
            raise

    def load_all(self):
        logging.info("Starting Load Phase...")
        try:
            self.connect()
            self.create_tables()

            df_dim_artists = pd.read_csv(os.path.join(self.processed_data_path, "dim_artists.csv"))
            df_dim_albums = pd.read_csv(os.path.join(self.processed_data_path, "dim_albums.csv"))
            df_fact_tracks = pd.read_csv(os.path.join(self.processed_data_path, "fact_tracks.csv"))

            self.upsert_dataframe(df_dim_artists, "dim_artists", "artist_id")
            self.upsert_dataframe(df_dim_albums, "dim_albums", "album_id")
            self.upsert_dataframe(df_fact_tracks, "fact_tracks", "track_id")

            logging.info("Phase 6: Load completed successfully. Data is now in PostgreSQL.")

        except FileNotFoundError as e:
            logging.error(f"Missing processed CSV file: {e}. Run transform.py first.")
        except Exception as e:
            logging.critical(f"Load failed: {e}")
        finally:
            self.close()


if __name__ == "__main__":
    loader = DeezerLoader()
    loader.load_all()