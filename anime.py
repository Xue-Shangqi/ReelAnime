import psycopg

class Anime:
    def __init__(self, anime_id:int, name:str, episodes:int, type:str, english_name:str, score:float, studios:str, source:str, image:str):
        self.anime_id = anime_id
        self.name = name
        self.english_name = english_name
        self.episodes = episodes
        self.type = type
        self.score = score
        self.source = source
        self.image = image
        self.studios = studios
        self.genres = []

    def GetAllInfo(self) -> dict:
        return {
            "anime_id": self.anime_id,
            "name": self.name,
            "english_name": self.english_name,
            "episodes": self.episodes,
            "type": self.type,
            "score": self.score,
            "studios": self.studios,
            "source": self.source,
            "image": self.image,
            "genres": self.genres
        }

    def FillGenres(self):
        with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
            queryGenre = """
                    SELECT * FROM animegenre
                    WHERE anime_id = %s
                """
            queryGenreName = """
                    SELECT * FROM genres
                    WHERE genre_id = %s
                """
            with conn.cursor() as cursor:
                cursor.execute(queryGenre, (self.anime_id,))
                result = cursor.fetchall()

                for row in result:
                    genre_id = row[1]
                    cursor.execute(queryGenreName, (genre_id,))
                    genres = cursor.fetchone()

                    self.genres.append(genres[1])