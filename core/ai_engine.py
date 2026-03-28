from .models import CachedPlayer, Match
from django.db.models import Q


def safe_number(value):
    """
    Convert value safely to float.
    Handles 'N/A', '-', '', etc.
    """
    try:
        return float(value)
    except:
        return 0


def get_player_score(player_data):

    stats = player_data.get("stats", [])

    runs = 0
    wickets = 0

    if isinstance(stats, list):

        for s in stats:

            stat = s.get("stat", "").lower()
            value = safe_number(s.get("value"))

            if "run" in stat:
                runs += value

            if "wicket" in stat:
                wickets += value


    elif isinstance(stats, dict):

        for match_type in stats.values():

            for stat, value in match_type.items():

                val = safe_number(value)

                if "run" in stat.lower():
                    runs += val

                if "wicket" in stat.lower():
                    wickets += val


    # weighted score
    return runs * 0.6 + wickets * 0.4



def team_strength(team_name):

    players = CachedPlayer.objects.filter(
        data__team__icontains=team_name
    )

    total_score = 0

    for p in players:

        total_score += get_player_score(p.data)

    # fallback if no players cached
    if total_score == 0:
        total_score = 50

    return total_score



def recent_form(team):

    matches = Match.objects.filter(
        Q(team1__name=team) | Q(team2__name=team)
    ).order_by("-match_number")[:5]


    wins = sum(
        1 for m in matches
        if m.winner and m.winner.name == team
    )

    return wins * 15   # weight recent form



def predict_match_ai(team1, team2):

    s1 = team_strength(team1) + recent_form(team1)
    s2 = team_strength(team2) + recent_form(team2)

    total = s1 + s2 if (s1 + s2) != 0 else 1

    t1_prob = (s1 / total) * 100
    t2_prob = (s2 / total) * 100

    winner = team1 if t1_prob > t2_prob else team2


    confidence = "Low"

    diff = abs(t1_prob - t2_prob)

    if diff > 25:
        confidence = "High"
    elif diff > 12:
        confidence = "Medium"


    return {
        "winner": winner,
        "team1_prob": round(t1_prob, 2),
        "team2_prob": round(t2_prob, 2),
        "confidence": confidence
    }