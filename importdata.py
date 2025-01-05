import pandas as pd
import psycopg

class ImportData:
    def cleanData(self, filePath) -> pd.DataFrame:
        df = pd.read_csv(filePath)
        df['score'] = pd.to_numeric(df['score'], errors='coerce')
        df['episodes'] = pd.to_numeric(df['episodes'], errors='coerce', downcast='integer')

        df_cleaned = df.dropna(subset=['score', 'episodes'])
        df_cleaned.reset_index(drop=True, inplace=True)
        return df_cleaned
    
    def importAnimeData(self, filePath):
        with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
            df = self.cleanData(filePath)
            insert_query = """
                        INSERT INTO anime (anime_id, name, english_name, score, type, episodes, studios, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO NOTHING;  -- Skip duplicates
                        """
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    cur.execute(insert_query, (
                        int(row['anime_id']),
                        row['name'],
                        row['english_name'],
                        float(row['score']) if row['score'] else None,
                        row['type'],
                        int(row['episodes']) if row['episodes'] else None,
                        row['studios'],
                        row['source']
                    ))
                conn.commit()
                print("anime data imported successfully.")

    def importAnimeGenres(animeGenres, genres):
        with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
            ag = pd.read_csv(animeGenres)
            g = pd.read_csv(genres)
            insert_ag_query = """
                        INSERT INTO animegenre (anime_id, genre_id)
                        VALUES (%s, %s)
                        """
            insert_g_query = """
                        INSERT INTO genres (genre_id, genre)
                        VALUES (%s, %s)
                        """
            with conn.cursor() as cur:
                for _, row in ag.iterrows():
                    cur.execute(insert_ag_query, (
                        int(row['anime_id']),
                        int(row['genre_id'])
                    ))
                
                for _, row in g.iterrows():
                    cur.execute(insert_g_query, (
                        int(row['genre_id']),
                        row['genre']
                    ))
                conn.commit()
                print("anime genres imported successfully.")

    def importAnimeImages(self, filePath):
        with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
            df = pd.read_csv(filePath)
            insert_query = """
                        INSERT INTO animeimage (anime_id, image_url)
                        VALUES (%s, %s)
                        """
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    cur.execute(insert_query, (
                        int(row['anime_id']),
                        row['image_url']
                    ))
                conn.commit()
                print("image data imported successfully.")