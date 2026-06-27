# 3. transform.py

import os
import json
import pandas as pd
import logging

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


class DeezerTransformer:
    def __init__(self):
        self.raw_data_path = "data/raw_data"
        self.processed_data_path = "data/processed_data"
        os.makedirs(self.processed_data_path, exist_ok=True)
        logging.info("DeezerTransformer Engine Initialized.")

    def load_master_chart(self):
        file_path = os.path.join(self.raw_data_path, "songs", "top_tracks_chart.json")
        if not os.path.exists(file_path):
            logging.error(f"Master file not found at {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def transform_data(self):
        logging.info("Starting Data Transformation and Flattening Process...")

        master_data = self.load_master_chart()
        if not master_data or 'data' not in master_data:
            logging.critical("Transformation failed: No data available.")
            return

        tracks_list = master_data['data']

        fact_tracks_data = []
        for track in tracks_list:
            fact_tracks_data.append({
                "track_id": track['id'],
                "artist_id": track['artist']['id'],
                "album_id": track['album']['id'],
                "title": track.get('title', None),
                "duration": track.get('duration', None),
                "rank": track.get('rank', None),
                "explicit_lyrics": track.get('explicit_lyrics', None)
            })

  
        df_fact_tracks = pd.DataFrame(fact_tracks_data).drop_duplicates(subset=['track_id'])


        artists_data = []
        artist_folder = os.path.join(self.raw_data_path, "artists")

        if os.path.exists(artist_folder):
            for filename in os.listdir(artist_folder):
                if filename.endswith(".json"):
                    with open(os.path.join(artist_folder, filename), 'r', encoding='utf-8') as f:
                        art = json.load(f)
                        if 'error' not in art:
                            artists_data.append({
                                "artist_id": art['id'],
                                "artist_name": art['name'],
                                "nb_album": art.get('nb_album', 0),
                                "nb_fan": art.get('nb_fan', 0)
                            })
        df_dim_artists = pd.DataFrame(artists_data).drop_duplicates(subset=['artist_id'])

   
        albums_data = []
        album_folder = os.path.join(self.raw_data_path, "albums")

        if os.path.exists(album_folder):
            for filename in os.listdir(album_folder):
                if filename.endswith(".json"):
                    with open(os.path.join(album_folder, filename), 'r', encoding='utf-8') as f:
                        alb = json.load(f)
                        if 'error' not in alb:
                            albums_data.append({
                                "album_id": alb['id'],
                                "album_title": alb['title'],
                                "release_date": alb.get('release_date', None),
                                "genre_id": alb.get('genres', {}).get('data', [{}])[0].get('id', None)
                                if alb.get('genres', {}).get('data') else None
                            })
        df_dim_albums = pd.DataFrame(albums_data).drop_duplicates(subset=['album_id'])

        logging.info(f"Transformed Fact Tracks Shape: {df_fact_tracks.shape}")
        logging.info(f"Transformed Dim Artists Shape: {df_dim_artists.shape}")
        logging.info(f"Transformed Dim Albums Shape: {df_dim_albums.shape}")

   
        missing_artists = set(df_fact_tracks['artist_id']) - set(df_dim_artists['artist_id'])
        missing_albums = set(df_fact_tracks['album_id']) - set(df_dim_albums['album_id'])
        if missing_artists:
            logging.warning(f"Fact table references {len(missing_artists)} artist_id(s) with no dimension row: {missing_artists}")
        if missing_albums:
            logging.warning(f"Fact table references {len(missing_albums)} album_id(s) with no dimension row: {missing_albums}")

     
        rows_before = len(df_fact_tracks)
        df_fact_tracks = df_fact_tracks[
            df_fact_tracks['artist_id'].isin(df_dim_artists['artist_id']) &
            df_fact_tracks['album_id'].isin(df_dim_albums['album_id'])
        ]
        rows_dropped = rows_before - len(df_fact_tracks)
        if rows_dropped:
            logging.warning(f"Dropped {rows_dropped} fact_tracks row(s) with missing artist/album dimension data.")

        
        df_fact_tracks.to_csv(os.path.join(self.processed_data_path, "fact_tracks.csv"), index=False)
        df_dim_artists.to_csv(os.path.join(self.processed_data_path, "dim_artists.csv"), index=False)
        df_dim_albums.to_csv(os.path.join(self.processed_data_path, "dim_albums.csv"), index=False)

        logging.info("Phase 5: Transformation Engine completed successfully. Data Staged as CSVs.")


if __name__ == "__main__":
    transformer = DeezerTransformer()
    transformer.transform_data()