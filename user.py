import psycopg
from anime import Anime

class User:
    def __init__(self, uid:int=None, uname:str=None, password:str=None):
        self.user_id = uid
        self.username = uname
        self.password = password
        self.LikeList = []

    def AddToLikingList(self, anime_id):
        with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
            check_query = """
                SELECT 1 FROM userlikes
                WHERE user_id = %s AND anime_id = %s
            """
            with conn.cursor() as cursor:
                cursor.execute(check_query, (self.user_id, anime_id))
                result = cursor.fetchone()
                
                if result is None:
                    insert_query = """
                        INSERT INTO userlikes (user_id, anime_id)
                        VALUES (%s, %s)
                    """
                    cursor.execute(insert_query, (self.user_id, anime_id))
                    conn.commit()
                    self.GetAnimeInfo(anime_id)

    
    def GetLikingList(self):
        self.LikeList.clear()
        if self.user_id:
            with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
                queryLiking = """
                    SELECT * FROM userlikes
                    WHERE user_id = %s
                """
                with conn.cursor() as cursor:
                    cursor.execute(queryLiking, (self.user_id,))
                    result = cursor.fetchall()

                    for row in result:
                        anime_id = row[1]
                        self.GetAnimeInfo(anime_id)


    def ValidUser(self, uname, password) -> bool:
        if uname is not None and password is not None:
            with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
                query = """
                    SELECT user_id FROM users
                    WHERE username = %s AND password = %s
                """
                with conn.cursor() as cursor:
                    cursor.execute(query, (uname, password))
                    result = cursor.fetchone()
                    if result:
                        self.user_id = result[0]
                        self.username = uname
                        self.password = password
                        return True
        return False
                    
    def CreateUser(self, uname, password):
        self.username = uname
        self.password = password

        with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
            with conn.cursor() as cursor:
                queryCreate = """
                    INSERT INTO users (username, password) 
                    VALUES (%s, %s)
                """
                querySelect = """
                    SELECT user_id FROM users
                    WHERE username = %s AND password = %s
                """
                cursor.execute(queryCreate, (self.username, self.password))
                cursor.execute(querySelect, (self.username, self.password))
                self.user_id = cursor.fetchone()[0]
                conn.commit()

    def GetAnimeInfo(self, anime_id):
        with psycopg.connect("dbname=finalproject user=postgres password=shang") as conn:
                queryAnimeInfo = """
                    SELECT * FROM anime
                    WHERE anime_id = %s
                """
                queryAnimeImage = """
                    SELECT * FROM animeimage
                    WHERE anime_id = %s
                """

                with conn.cursor() as cursor:
                    cursor.execute(queryAnimeInfo, (anime_id,))
                    anime_data = cursor.fetchone()

                    cursor.execute(queryAnimeImage, (anime_id,))
                    image_data = cursor.fetchone()
                    anime = Anime(
                        int(anime_data[0]),
                        anime_data[1],
                        int(anime_data[2]),
                        anime_data[3],
                        anime_data[4],
                        float(anime_data[5]),
                        anime_data[6],
                        anime_data[7],
                        image_data[1]
                    )
                    anime.FillGenres()
                    self.LikeList.append(anime)
                    return anime