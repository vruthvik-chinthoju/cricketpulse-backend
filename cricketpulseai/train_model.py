import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib


df = pd.read_csv("Cricket_data.csv")


df = df[[
    "home_team",
    "away_team",
    "toss_won",
    "decision",
    "venue_name",
    "winner"
]]


df = df.dropna().reset_index(drop=True)



def get_head_to_head_safe(df):
    h2h_list = []

    for i in range(len(df)):
        row = df.iloc[i]
        past = df.iloc[:i]

        matches = past[
            ((past["home_team"] == row["home_team"]) & (past["away_team"] == row["away_team"])) |
            ((past["home_team"] == row["away_team"]) & (past["away_team"] == row["home_team"]))
        ]

        team1_wins = len(matches[matches["winner"] == row["home_team"]])
        team2_wins = len(matches[matches["winner"] == row["away_team"]])

        h2h_list.append(team1_wins - team2_wins)

    return h2h_list


df["head_to_head"] = get_head_to_head_safe(df)



encoders = {}

for col in ["home_team", "away_team", "toss_won", "decision", "venue_name", "winner"]:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le



X = df[[
    "home_team",
    "away_team",
    "toss_won",
    "decision",
    "venue_name",
    "head_to_head"
]]

y = df["winner"]


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


model = RandomForestClassifier(
    n_estimators=120,
    max_depth=20,
    min_samples_split=3,
    n_jobs=-1
)

model.fit(X_train, y_train)



accuracy = model.score(X_test, y_test)
print("🔥 Accuracy:", round(accuracy * 100, 2), "%")



joblib.dump(model, "model.pkl")
joblib.dump(encoders, "encoders.pkl")

print("Model & encoders saved successfully!")


raw_df = pd.read_csv("Cricket_data.csv")

def calculate_head_to_head(team1, team2, df):
    matches = df[
        ((df["home_team"] == team1) & (df["away_team"] == team2)) |
        ((df["home_team"] == team2) & (df["away_team"] == team1))
    ]

    team1_wins = len(matches[matches["winner"] == team1])
    team2_wins = len(matches[matches["winner"] == team2])

    return team1_wins - team2_wins


test_input = {
    "home_team": "RCB",
    "away_team": "MI",
    "toss_won": "RCB",
    "decision": "BOWL FIRST",  
    "venue_name": "M.Chinnaswamy Stadium, Bengaluru"
}


h2h = calculate_head_to_head(
    test_input["home_team"],
    test_input["away_team"],
    raw_df
)


def safe_transform(encoder, value):
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    else:
        print(f" Unknown value: {value}")
        return 0


encoded = [
    safe_transform(encoders["home_team"], test_input["home_team"]),
    safe_transform(encoders["away_team"], test_input["away_team"]),
    safe_transform(encoders["toss_won"], test_input["toss_won"]),
    safe_transform(encoders["decision"], test_input["decision"]),
    safe_transform(encoders["venue_name"], test_input["venue_name"]),
    h2h
]


prediction = model.predict([encoded])
winner = encoders["winner"].inverse_transform(prediction)

print("Predicted Winner:", winner[0])