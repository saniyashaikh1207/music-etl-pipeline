# 2. explore.py
import json
import os
import pandas as pd


def explore_raw_chart():
    file_path = "data/raw_data/songs/top_tracks_chart.json"

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found! Run the extractor first.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"1. Top Level JSON Keys: {list(data.keys())}")
    print(f"2. Total Tracks Found in File: {len(data['data'])}\n")

    df = pd.DataFrame(data['data'])
    print("3. Tracks DataFrame Shape (Rows, Columns):", df.shape)

    print("\n4. First 3 Rows Preview:")
    print(df[['id', 'title', 'duration', 'rank']].head(3))

    print("\n5. DataFrame Info (Data Types & Null Values):")
    print(df.info())

   
    print("\n6. Analyzing Nested Structures:")
    first_track = data['data'][0]
    print(f"Track Title: {first_track['title']}")
    print(f"Artist Nested Key Structure: {first_track['artist'].keys()} -> Sample: {first_track['artist']}")
    print(f"Album Nested Key Structure: {first_track['album'].keys()} -> Sample: {first_track['album']}")


if __name__ == "__main__":
    explore_raw_chart()