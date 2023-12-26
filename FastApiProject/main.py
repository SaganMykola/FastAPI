import psycopg2
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import random


app = FastAPI()

connection = psycopg2.connect(
    host='localhost',
    port='5432',
    user='kolya',
    password='14756SAG',
    database='postgres'
)


@app.post("/create_table_games")
def create_table_games():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                status VARCHAR(50),
                winner_id INTEGER REFERENCES players(id),
                timestamp_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timestamp_end TIMESTAMP,
                game_state JSONB
            )
            """
            cursor.execute(sql)
        connection.commit()


@app.post("/create_table_dominoes")
def create_table_dominoes():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS dominoes (
                id SERIAL PRIMARY KEY,
                half_1 INT,
                half_2 INT
            )
            """
            cursor.execute(sql)
        connection.commit()

@app.post("/create_table_players")
def create_table_players():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200),
                user_id INTEGER REFERENCES users(id)
            )
            """
            cursor.execute(sql)
        connection.commit()

@app.post("/create_table_player_dominoes")
def create_table_player_dominoes():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS player_dominoes (
                id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(id),
                domino_id INTEGER REFERENCES dominoes(id)
            )
            """
            cursor.execute(sql)
        connection.commit()

@app.post("/create_table_board_dominoes")
def create_table_board_dominoes():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS board_dominoes (
                id SERIAL PRIMARY KEY,
                domino_id INTEGER REFERENCES dominoes(id)
            )
            """
            cursor.execute(sql)
        connection.commit()

@app.post("/create_table_game_history")
def create_table_game_history():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS game_history (
                id SERIAL PRIMARY KEY,
                game_id INTEGER REFERENCES games(id),
                player_id INTEGER REFERENCES players(id),
                turn_number INTEGER,
                action_type VARCHAR(50),
                action_description VARCHAR(1000),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(sql)
        connection.commit()

@app.post("/create_table_scores")
def create_table_scores():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS scores (
                id SERIAL PRIMARY KEY,
                game_id INTEGER REFERENCES games(id),
                player_id INTEGER REFERENCES players(id),
                score INTEGER
            )
            """
            cursor.execute(sql)
        connection.commit()

class User(BaseModel):
    name: str

class Domino(BaseModel):
    half_1: int
    half_2: int

class Player(BaseModel):
    id: int
    name: str
    user_id: int

class Game(BaseModel):
    player_id: int
    status: str

class Score(BaseModel):
    game_id: int
    player_id: int
    score: int


class Token(BaseModel):
    access_token: str
    token_type: str


class RegisterData(BaseModel):
    email: str
    username: str
    password: str


class LoginData(BaseModel):
    username: str
    password: str


def get_token(authorization: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    return authorization

tokens_db = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/register", response_model=Token)
async def register(data: RegisterData):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (data.username,))
            existing_user = cursor.fetchone()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Користувач з таким ім'ям вже існує",
        )

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (email, username, password) VALUES (%s, %s, %s) RETURNING id", (data.email, data.username, data.password))
            user_id = cursor.fetchone()[0]

    access_token = f"fake_access_token_{data.username}"
    token_type = "bearer"
    tokens_db[access_token] = user_id

    return {"access_token": access_token, "token_type": token_type}
@app.post("/login", response_model=Token)
async def login(data: LoginData):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (data.username, data.password))
            existing_user = cursor.fetchone()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильні дані для входу",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = existing_user[0]

    access_token = f"fake_access_token_{data.username}"
    token_type = "bearer"
    tokens_db[access_token] = user_id

    return {"access_token": access_token, "token_type": token_type}

@app.get("/")
def read_root():
    return {"Hello World"}

def generate_dominoes():
    dominoes = []
    for i in range(1, 7):
        for j in range(1, 7):
            dominoes.append((i, j))
    return dominoes

@app.post("/generate_dominoes/")
def generate_dominoes():
    db_dominoes = generate_dominoes()
    try:
        with connection:
            with connection.cursor() as cursor:
                for half_1, half_2 in db_dominoes:
                    sql = "INSERT INTO dominoes (half_1, half_2) VALUES (%s, %s)"
                    cursor.execute(sql, (half_1, half_2))
    finally:
        connection.close()

    return {
        "result": "ok",
        "message": "Доміно створено",
    }

@app.post("/create_player", response_model=dict)
def create_player(player_data: Player):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO players (name, user_id) VALUES (%s, %s) RETURNING id",
                (player_data.name, player_data.user_id),
            )

    return {
        "result": "ok",
        "message": "Користувача створено",
    }

@app.post("/start_game")
def start_game(game: Game, player: Player):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM players WHERE id = %s", (player.id,))
            existing_player = cursor.fetchone()

            if not existing_player:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Гравець не знайдений",
                )

            cursor.execute("INSERT INTO games (status, timestamp_start) VALUES (%s, CURRENT_TIMESTAMP) RETURNING id", ("active",))
            game_id = cursor.fetchone()[0]

            cursor.execute("SELECT * FROM dominoes")
            available_dominoes = cursor.fetchall()

            random.shuffle(available_dominoes)
            player_dominoes = available_dominoes[:6]

            for domino in player_dominoes:
                cursor.execute("INSERT INTO player_dominoes (player_id, domino_id) VALUES (%s, %s) RETURNING id", (existing_player.id, domino[0]))

                cursor.execute("INSERT INTO board_dominoes (domino_id) VALUES (%s) RETURNING id", (domino[0],))

    return {
        "result": "ok",
        "message": "Гра створена",
    }