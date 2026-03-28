import json
from core.models import Match, Team
from datetime import datetime

with open("core/data/matches.json") as f:
    matches = json.load(f)

for m in matches:

    team1 = Team.objects.get(name=m["team1"])
    team2 = Team.objects.get(name=m["team2"])

    match_datetime = datetime.strptime(
        f"{m['date']} {m['time']}",
        "%Y-%m-%d %H:%M"
    )

    Match.objects.update_or_create(
        match_number=m["match_number"],
        team1=team1,
        team2=team2,
        venue=m["venue"],
        match_date=match_datetime
    )

print("Matches inserted successfully!")