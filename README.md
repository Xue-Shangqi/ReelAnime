# ReelAnime #
This project reommenders different anime based on what user's anime like list. The machine learning algorithm for used for recommendation is KNN. The algorithm basically takes different elements from liked anime and map them out to see other anime that are similar on a graph. The project requires the use of a PostgreSQL database to store and retrieve data from. 
- Please set up the database with the correct pg_dumps
- Please run pip install -r requirements.txt

To run the code, type into the terminal:
    streamlit run app.py

You have to create an account first if you dont have an account. If you have an account, just login.
This project is suppose to be an anime recommendation system, before the system can recommend you anything,
you have to add some anime into your like list. It will generate 3 similar anime for each corresponding anime 
in your like list. The recommendation ML algorithm is not the most accurate ML model, so some recommendations 
might be inaccurate. 

Thank you!
