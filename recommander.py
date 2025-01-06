import os
import psycopg
import pandas as pd
from anime import Anime
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import NearestNeighbors

class Recommander:
    def __init__(self, k=5):
        self.k = k
        self.knn_model = NearestNeighbors(n_neighbors=self.k, metric='cosine')
        self.encoder = OneHotEncoder()
        self.data = None
        self.indices_to_ids = {}  
        self.ids_to_names = {}  

    def ReadData(self, filePath, conn: psycopg.Connection):
        if os.path.isfile(filePath):
            df = pd.read_csv(filePath)
            return df
        else:   
            db = None
            match filePath:
                case "data/anime_dataset.csv":
                    db = "anime"
                case "data/anime_genres.csv":
                    db = "animegenre"
                case "data/anime_images.csv":
                    db = "animeimage"
                case _:
                    print("Invalid path")

            if db:
                query = f"SELECT * FROM {db};"
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    col_names = [desc[0] for desc in cur.description]
                
                df = pd.DataFrame(rows, columns=col_names)
                df.to_csv(filePath, index=False)
                return df

    def PreProcessing(self, conn: psycopg.Connection):
        anime_df = self.ReadData("data/anime_dataset.csv", conn)
        genres_df = self.ReadData("data/anime_genres.csv", conn)

        if anime_df is not None and genres_df is not None:
            # One-hot encode genres
            genres_encoded = pd.get_dummies(genres_df['genre_id'], prefix="genre")
        
            # Combine one-hot encoded genres with the anime dataframe
            genre_matrix = genres_encoded.groupby(genres_df['anime_id']).max()

            # Merge the two dataframe togethe and drop anime where genre is unknown
            df = anime_df.merge(genre_matrix, on="anime_id", how="left")
            df.dropna(inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            # Combine the different features
            feature_columns = ['score', 'episodes'] + list(genre_matrix.columns)
            features = df[feature_columns]

            # Use to keep track of indices, anime id, anime name
            self.indices_to_ids = df['anime_id'].to_dict()
            self.ids_to_names = df.set_index('anime_id')['name'].to_dict()

            self.data = features
            return self.data
        else:
            print("Data could not be loaded")
            return None
        
    def TrainModel(self):
        if self.data is not None:
            self.knn_model.fit(self.data)
        else:
            print("Data not processed. Run PreProcessing first.")

    def Recommend(self, anime_ids, conn: psycopg.Connection):
        if self.data is not None:
            if isinstance(anime_ids, list):
                recommendations = []
                for anime_id in anime_ids:
                    if anime_id in self.indices_to_ids.values():
                        # Find the index of the anime_id
                        index = list(self.indices_to_ids.values()).index(anime_id)

                        # Retrieve the feature vector for the anime and convert to DataFrame
                        query_vector = self.data.iloc[index:index+1]

                        # Get the nearest neighbors
                        distances, indices = self.knn_model.kneighbors(query_vector)

                        # Map indices back to anime IDs and names
                        anime_recommendations = []
                        for _,idx in enumerate(indices[0]):
                            idx_anime_id = self.indices_to_ids[idx]
                            if idx_anime_id != anime_id:
                                anime_recommendations.append((idx_anime_id))
                        recommendations.append((anime_recommendations))
                    else:
                        print(f"Anime ID {anime_id} not found in dataset.")

                # Convert the recommendations into anime object after query for all the data 
                queryAnime = """
                    SELECT * FROM anime
                    WHERE anime_id = ANY(%s)
                """
                queryAnimeImage = """
                    SELECT * FROM animeimage
                    WHERE anime_id = ANY(%s)
                """

                recommendationsObj = []
                with conn.cursor() as cursor:
                    for sublist in recommendations:
                        cursor.execute(queryAnime, (list(sublist),))
                        animeresult = cursor.fetchall()
                        cursor.execute(queryAnimeImage, (list(sublist),))
                        imageresult = cursor.fetchall()

                        tempList = []
                        for i, data in enumerate(animeresult):
                            anime = Anime(
                                int(data[0]),
                                data[1],
                                int(data[2]),
                                data[3],
                                data[4],
                                float(data[5]),
                                data[6],
                                data[7],
                                imageresult[i][1]
                            )
                            tempList.append(anime)
                        recommendationsObj.append(tempList)
                return recommendationsObj
            else:
                print("Input should be a list of anime IDs.")
        else:
            print("Model not trained. Run TrainModel first.")