# 1. extract.py
import os
import json
import time
import requests
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


class DeezerExtractor:
    PLAYLIST_ID = "3155776842"  
    def __init__(self):
        self.base_url = "https://api.deezer.com"
        self.raw_data_path = "data/raw_data"

   
    def fetch_data(self, endpoint, params=None, max_retries=3):
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(1, max_retries + 1):
            logging.info(f"Fetching -> {url} (attempt {attempt}/{max_retries})")
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=15
                )

                logging.info(f"Status Code : {response.status_code}")

                if response.status_code == 200:

                    res_json = response.json()

                    if "error" in res_json:

                        logging.error(
                            f"Deezer API Error : {res_json['error']['message']}"
                        )

                        # Rate Limit -> wait and retry (bounded by max_retries)
                        if res_json["error"]["code"] == 4:
                            logging.warning(
                                f"Rate limit reached. Waiting 5 seconds... "
                                f"(retry {attempt}/{max_retries})"
                            )
                            time.sleep(5)
                            continue
                        return None
                    return res_json
                else:
                    logging.error(f"HTTP Error : {response.status_code}")
                    return None

            except Exception as e:
                logging.error(f"Request Failed : {e}")
                return None

        logging.error(f"Max retries exceeded for endpoint: {endpoint}")
        return None

    def save_json(self, data, category, filename):
        dir_path = os.path.join(self.raw_data_path, category)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )
        logging.info(
            f"Saved {category} -> {filename}"
        )

    def extract_top_tracks(self):
        logging.info("Starting connection to Deezer Playlist API...")
        chart_data = self.fetch_data(
            f"playlist/{self.PLAYLIST_ID}/tracks",
            params={"limit": 50}
        )
        if not chart_data or 'data' not in chart_data:
            logging.error("Extraction aborted: No chart data could be retrieved.")
            return
        self.save_json(chart_data, "songs", "top_tracks_chart.json")

        total_tracks = len(chart_data['data'])
        logging.info(f"Total Tracks Found : {total_tracks}")

        for track in chart_data['data']:
            track_id = track['id']
            artist_id = track['artist']['id']
            album_id = track['album']['id']

            logging.info(f"Processing Track ID {track_id} | Artist: {track['artist']['name']}")


            artist_file = os.path.join(self.raw_data_path, "artists", f"artist_{artist_id}.json")
            if os.path.exists(artist_file):
                logging.info(f"Artist {artist_id} already cached, skipping fetch.")
            else:
                artist_data = self.fetch_data(f"artist/{artist_id}")
                if artist_data:
                    self.save_json(artist_data, "artists", f"artist_{artist_id}.json")

            
            album_file = os.path.join(self.raw_data_path, "albums", f"album_{album_id}.json")
            if os.path.exists(album_file):
                logging.info(f"Album {album_id} already cached, skipping fetch.")
            else:
                album_data = self.fetch_data(f"album/{album_id}")
                if album_data:
                    self.save_json(album_data, "albums", f"album_{album_id}.json")

            time.sleep(0.2)

        logging.info("Phase 1 & Phase 2: Ingestion and Raw Storage Completed Successfully!")

=
if __name__ == "__main__":

    extractor = DeezerExtractor()
    extractor.extract_top_tracks() 