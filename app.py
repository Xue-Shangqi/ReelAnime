from user import User
from recommander import Recommander
from streamlit_searchbox import st_searchbox
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import os
import psycopg


class App:
    def __init__(self, conn: psycopg.Connection):
        self.conn = conn
        if "user" not in st.session_state:
            st.session_state["user"] = User()
        
        if "current_view" not in st.session_state:
            st.session_state["current_view"] = "login"

        if st.session_state["current_view"] == "main_menu":
            os.makedirs("data/", exist_ok=True)
            if not os.path.isfile("data/anime_dataset.csv",):
                r = Recommander()
                r.ReadData("data/anime_dataset.csv", self.conn)
            self.anime_df = pd.read_csv("data/anime_dataset.csv", usecols=["anime_id", "name", "english_name"]) # Preload the data


    def expandButton(self, *args, key=None, **kwargs):
        if key is None: raise ValueError("Missing button key")
        if key not in st.session_state: st.session_state[key] = False

        if st.button(*args, **kwargs):
            st.session_state[key] = not st.session_state[key]
            st.rerun()

        return st.session_state[key]

    def loginPage(self):
        st.set_page_config(layout="centered")

        # Login
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Login")

        if login_submit:
            if st.session_state["user"].ValidUser(username, password, self.conn):
                st.session_state["current_view"] = "main_menu"
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
        st.divider()

        # Register
        if self.expandButton("Register", key="register_expand_button"):
            st.subheader("Register")
            with st.form("register_form"):
                reg_username = st.text_input("Username", key="register_username")
                reg_password = st.text_input("Password", type="password", key="register_password")
                reg_confirmpassword = st.text_input("Confirm Password", type="password", key="register_confirmpassword")
                reg_submit = st.form_submit_button("Register")

            if reg_submit:
                if not reg_username or not reg_password:
                    st.error("Please enter both a username and password.")
                elif reg_password != reg_confirmpassword:
                    st.error("Passwords do not match.")
                else:
                    st.session_state["user"].CreateUser(reg_username, reg_confirmpassword, self.conn)
                    st.session_state["current_view"] = "main_menu"
                    st.success("Account successful created")
                    st.rerun()

    def mainMenu(self):
        # Page setup
        st.set_page_config(layout="wide")
        
        # Title of page
        st.title(f"Welcome {st.session_state["user"].username}!")
        
        # Search box
        st.divider()
        st_searchbox(
            self.searchAnime,
            placeholder="Seach Anime...",
            key = "searchbox",
            clear_on_submit=True,
            submit_function=self.submitResult

        )
        st.divider()

        # Split page into 2 columns
        col1, col2 = st.columns([2, 3])

        # Display current liking list
        st.session_state["user"].GetLikingList(self.conn)
        col1.subheader("Current Like List")
        with col1.container(height=500):
            if st.session_state["user"].LikeList:
                like_list_data = [{
                    "Anime Name": anime.name,
                    "Genre": ", ".join(anime.genres),
                    "Rating": anime.score,
                } for anime in st.session_state["user"].LikeList]

                st.dataframe(like_list_data, hide_index=True, width=1000)
            else:
                st.write("No anime in the liking list.")

        # Logout button
        if col1.button("Logout"):
            st.session_state["current_view"] = "login"
            st.session_state["user"] = User()
            st.rerun()

        # Recommendation section
        col2.subheader("Recommendations")
        with col2.container(height=500):
            if st.button("Get Recommendation", key="recommendBtn", use_container_width=True):
                rec = Recommander(k= 4)
                rec.ReadData("data/anime_dataset.csv", self.conn)
                rec.ReadData("data/anime_genres.csv", self.conn)
                rec.ReadData("data/anime_images.csv", self.conn)
                rec.PreProcessing(self.conn)
                rec.TrainModel()

                anime_ids = [anime.anime_id for anime in st.session_state["user"].LikeList]
                recList = rec.Recommend(anime_ids, self.conn)
                
                for sublist in recList:
                    row = st.columns(3)
                    for i, col in enumerate(row):
                        tile = col.container(height=400)
                        tile.write(f"**{sublist[i].name}**")
                        tile.image(sublist[i].image)
        
        col2.write("Disclaimer: The machine learning model might not be the most accurate model, so there might be some inaccuracy on the recommendations! Thank you for understanding.")

    def searchAnime(self, searchterm: str) -> list:
        filtered_df = self.anime_df[
            self.anime_df["name"].str.contains(searchterm, case=False) |
            self.anime_df["english_name"].str.contains(searchterm, case=False)
        ]

        filtered_list = []
        amount = 7 if len(filtered_df) > 7 else len(filtered_df)

        for i in range(amount - 1):
            name = filtered_df["name"].iloc[i]
            english_name = filtered_df["english_name"].iloc[i]
            if  english_name == "UNKNOWN":
                filtered_list.append(name)
            else:
                filtered_list.append(f"{name} ({english_name})")

        return filtered_list if len(filtered_list) > 0 else []
    
    def submitResult(self, result: str):
        name = result
        english_name = "UNKNOWN"
        start_idx = result.find("(")
        end_idx = result.find(")")

        if start_idx != -1 and end_idx != -1:
            name = result[:start_idx].strip()
            english_name = result[start_idx + 1:end_idx].strip()

        matching_row = self.anime_df[
            (self.anime_df["name"] == name) | 
            (self.anime_df["english_name"] == english_name)
        ]
        anime_id = matching_row["anime_id"].iloc[0]
        st.session_state["user"].AddToLikingList(int(anime_id), self.conn)
    
def get_db_config():
    load_dotenv("secret.env")
    if os.getenv("DB_HOST"):
        return {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "name": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }
    else:  # Fallback to Streamlit secrets
        return {
            "host": st.secrets["host"],
            "port": st.secrets["port"],
            "name": st.secrets["name"],
            "user": st.secrets["user"],
            "password": st.secrets["password"],
        }


def main():
    # get db config
    db_config = get_db_config()
    conn_str = (
        f"host={db_config['host']} "
        f"port={db_config['port']} "
        f"dbname={db_config['name']} "
        f"user={db_config['user']} "
        f"password={db_config['password']}"
    )

    try:
        with psycopg.connect(conn_str) as conn:
            app = App(conn)
            if st.session_state["current_view"] == "login":
                app.loginPage()
            elif st.session_state["current_view"] == "main_menu":
                app.mainMenu()
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
