import joblib
import pandas as pd
import os



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR, "model.pkl"))

encoders = joblib.load(os.path.join(BASE_DIR, "encoders.pkl"))

df = pd.read_csv(os.path.join(BASE_DIR, "Cricket_data.csv"))



def calculate_head_to_head(team1, team2):
    matches = df[
        ((df["home_team"] == team1) & (df["away_team"] == team2)) |
        ((df["home_team"] == team2) & (df["away_team"] == team1))
    ]

    team1_wins = len(matches[matches["winner"] == team1])
    team2_wins = len(matches[matches["winner"] == team2])

    return team1_wins - team2_wins


def safe_transform(encoder, value):
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    return 0


def predict_match(data):
    h2h = calculate_head_to_head(data["home_team"], data["away_team"])

    encoded = [
        safe_transform(encoders["home_team"], data["home_team"]),
        safe_transform(encoders["away_team"], data["away_team"]),
        safe_transform(encoders["toss_won"], data["toss_won"]),
        safe_transform(encoders["decision"], data["decision"]),
        safe_transform(encoders["venue_name"], data["venue_name"]),
        h2h
    ]

    prediction = model.predict([encoded])
    winner = encoders["winner"].inverse_transform(prediction)[0]


    proba = model.predict_proba([encoded])
    confidence = round(max(proba[0]) * 100, 2)

    return {
        "winner": winner,
        "confidence": confidence
    }