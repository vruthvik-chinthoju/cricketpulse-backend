from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status

from django.db.models import Count, Sum, F, Case, When, IntegerField, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from google.oauth2 import id_token
from google.auth.transport.requests import Request
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import os
from django.core.cache import cache

from .models import Match, Prediction, Team, CachedPlayer
from .serializers import MatchSerializer, PredictionSerializer, RegisterSerializer
from .ai_engine import predict_match_ai

from django.contrib.auth.models import User



API_KEY = "1775198c-0200-4142-80cc-ec951bf196f7"
User = get_user_model()


@api_view(['GET'])
def clear_player_cache(request):
    CachedPlayer.objects.all().delete()
    return Response({"message": "Cache cleared"})


def format_player_stats(stats):
    formatted = {}

    allowed = ["t20", "t20i", "ipl", "odi", "test"]

    mapping = {
        "m": "matches",
        "runs": "runs",
        "avg": "average",
        "sr": "strike_rate",
        "hs": "highest_score",
        "4s": "fours",
        "6s": "sixes",
        "50s": "fifties",
        "100s": "hundreds",
        "wkts": "wickets",
        "econ": "economy"
    }

    for s in stats:
        mt = s.get("matchtype", "").lower()
        stat = s.get("stat", "").lower()   # ✅ FIXED
        value = s.get("value")

        if mt not in allowed or not stat:
            continue

        if value in ["-", "", None, "N/A"]:
            continue

        try:
            if "." in str(value):
                value = float(value)
            else:
                value = int(value)
        except:
            pass

        if mt == "t20i":
            mt = "t20"

        clean_key = mapping.get(stat, stat)

        if mt not in formatted:
            formatted[mt] = {}

        if clean_key not in formatted[mt]:
            formatted[mt][clean_key] = value

    return formatted




@api_view(['GET'])
def get_player_info(request, player_id):

    refresh = request.GET.get("refresh")

    if not refresh:
        cached = CachedPlayer.objects.filter(player_id=player_id).first()
        if cached:
            return Response(cached.data)

    url = f"https://api.cricapi.com/v1/players_info?apikey={API_KEY}&id={player_id}"
    res = requests.get(url)
    data = res.json()

    if data.get("status") == "failure":
        return Response({"error": "API failed"}, status=500)

    player = data.get("data", data)

    stats = player.get("stats", [])

    player["formatted_stats"] = format_player_stats(stats) if stats else {}

    CachedPlayer.objects.update_or_create(
        player_id=player_id,
        defaults={"data": player}
    )

    return Response(player)




@api_view(['GET'])
def get_ipl_squads(request, year):

    cache_key = f"ipl_teams_{year}_v1"
    cached_data = cache.get(cache_key)

    if cached_data:
        # print("TEAMS CACHE HIT ✅")
        return Response(cached_data)

    # print("TEAMS FROM API ❌")

    series_map = {
        "2025": "d5a498c8-7596-4b93-8ab0-e0efc334531",
        "2024": "76ae85e2-88e5-4e99-83e4-5f352108aebc",
        "2023": "c75f8952-74d4-416f-b7b4-7da4b4e3ae6e",
        "2022": "47b54677-34de-4378-9019-154e82b9cc1a",
    }

    if year == "2025":
        year = "2023"

    series_id = series_map.get(str(year))

    if not series_id:
        return Response({"error": "Invalid year"}, status=400)

    url = f"https://api.cricapi.com/v1/series_squad?apikey={API_KEY}&id={series_id}"

    try:
        res = requests.get(url)
    except:
        return Response({"error": "API request failed"}, status=500)

    if res.status_code != 200:
        return Response({"error": "Bad API response"}, status=500)

    try:
        data = res.json()
    except:
        return Response({"error": "Invalid JSON"}, status=500)

    if data.get("status") == "failure":
        return Response({
            "error": "API failed",
            "reason": data.get("reason")
        }, status=400)

    cache.set(cache_key, data, timeout=60 * 60 * 6)

    return Response(data)





@api_view(['GET'])
def predict_match(request, match_id):

    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return Response({"error": "Match not found"}, status=404)

    result = predict_match_ai(match.team1.name, match.team2.name)

    return Response({
        "match": f"{match.team1.name} vs {match.team2.name}",
        "prediction": result
    })



@api_view(['POST'])
def chat_ai(request):

    msg = request.data.get("message", "").lower()

    if "team list" in msg:
        teams = Team.objects.all()
        names = [t.short_name for t in teams]

        return Response({"reply": "IPL Teams:\n" + ", ".join(names)})

    if "team stats" in msg:

        lines = []

        for team in Team.objects.all():
            total = Match.objects.filter(
                Q(team1=team) | Q(team2=team)
            ).count()

            wins = Match.objects.filter(winner=team).count()

            lines.append(f"{team.short_name}: {wins}/{total}")

        return Response({"reply": "\n".join(lines)})

    if "today" in msg:

        today = timezone.now().date()

        match = Match.objects.filter(match_date__date=today).first()

        if not match:
            return Response({"reply": "No match today."})

        result = predict_match_ai(match.team1.name, match.team2.name)

        return Response({
            "reply":
            f"{match.team1.short_name} vs {match.team2.short_name}\n"
            f"Winner: {result['winner']}\n"
            f"{result['team1_prob']}% vs {result['team2_prob']}%"
        })

    if "vs" in msg:

        parts = msg.split("vs")

        if len(parts) != 2:
            return Response({"reply": "Use format: CSK vs MI"})

        team1 = parts[0].strip().upper()
        team2 = parts[1].strip().upper()

        result = predict_match_ai(team1, team2)

        return Response({
            "reply":
            f"{team1} vs {team2}\n"
            f"Winner: {result['winner']}\n"
            f"{team1}: {result['team1_prob']}%\n"
            f"{team2}: {result['team2_prob']}%"
        })

    return Response({
        "reply": "Try: team list, team stats, predict today, CSK vs MI"
    })




class GoogleLogin(APIView):

    def post(self, request):

        token = request.data.get("credential")

        idinfo = id_token.verify_oauth2_token(
            token,
            Request(),
            "246111769075-p4r1ulljo9399ntck8b90per0uetrvtl.apps.googleusercontent.com",
        )

        email = idinfo["email"]

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0]}
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):

    return Response({
        "username": request.user.username,
        "email": request.user.email,
    })





@api_view(['GET'])
def match_list(request):

    matches = Match.objects.all().order_by("match_number")
    serializer = MatchSerializer(matches, many=True)

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_predictions(request):
    predictions = Prediction.objects.filter(user=request.user)
    serializer = PredictionSerializer(predictions, many=True)
    return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prediction(request):
    serializer = PredictionSerializer(data=request.data)

    if serializer.is_valid():
        match = serializer.validated_data["match"]
        predicted_winner = serializer.validated_data["predicted_winner"]
        if timezone.now() > match.match_date:
            return Response({"error": "Prediction closed"}, status=400)

        if Prediction.objects.filter(user=request.user, match=match).exists():
            return Response({"error": "Already predicted"}, status=400)

        prediction = Prediction.objects.create(
            user=request.user,
            match=match,
            predicted_winner=predicted_winner,
            prediction_deadline=match.match_date
        )

        return Response(PredictionSerializer(prediction).data, status=201)

    return Response(serializer.errors, status=400)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    data = Prediction.objects.values(
        "user__username"
    ).annotate(
        total_predictions=Count("id"),
        correct_predictions=Sum(
            Case(
                When(predicted_winner=F("match__winner"), then=1),
                default=0,
                output_field=IntegerField()
            )
        ),
        total_points=Sum("points")
    ).order_by("-total_points")

    result = []
    for i, user in enumerate(data, start=1):
        total = user["total_predictions"]
        correct = user["correct_predictions"] or 0

        accuracy = round((correct / total) * 100, 2) if total else 0

        result.append({
            "rank": i,
            "user": user["user__username"],
            "points": user["total_points"] or 0,
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        })

    return Response(result)

@api_view(['POST'])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created"}, status=201)
    
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def team_list(request):
    teams = Team.objects.all()

    data = []
    for team in teams:
        total_matches = Match.objects.filter(
            Q(team1=team) | Q(team2=team)
        ).count()

        wins = Match.objects.filter(winner=team).count()
        losses = total_matches - wins

        data.append({
            "id": team.id,
            "name": team.name,
            "short_name": team.short_name,
            "matches": total_matches,
            "wins": wins,
            "losses": losses,
            "win_percentage": round((wins / total_matches) * 100, 2) if total_matches else 0
        })

    return Response(data)


class GithubLogin(APIView):

    def post(self, request):
        code = request.data.get("code")

        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "code": code,
                "redirect_uri": "https://vruthvik-chinthoju.github.io/cricketpulse-frontend-v2/"
            },
            headers={"Accept": "application/json"}  

        )


        token_json = token_res.json()
        access_token = token_json.get("access_token")

        if not access_token:
            return Response({"error": "Failed to get access token"}, status=400)

        user_res = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        user_data = user_res.json()

        email = user_data.get("email")

        # GitHub sometimes doesn't return email → fix:
        if not email:
            email_res = requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            emails = email_res.json()
            primary = next((e for e in emails if e["primary"]), None)
            email = primary["email"] if primary else None

        if not email:
            return Response({"error": "Email not found"}, status=400)

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0]}
        )

        refresh = RefreshToken.for_user(user)



        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_match_winner(request, match_id):

    if not request.user.is_staff:
        return Response({"error": "Admin only"}, status=403)

    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return Response({"error": "Match not found"}, status=404)

    if match.winner:
        return Response({"error": "Winner already set"}, status=400)

    winner_id = request.data.get("winner")

    if not winner_id:
        return Response({"error": "Winner required"}, status=400)

    try:
        winner = Team.objects.get(id=winner_id)
    except Team.DoesNotExist:
        return Response({"error": "Invalid team"}, status=400)


    match.winner = winner
    match.status = "completed" 
    match.save()


    Prediction.objects.filter(
        match=match,
        predicted_winner=winner
    ).update(points=10)

    Prediction.objects.filter(
        match=match
    ).exclude(predicted_winner=winner).update(points=0)

    return Response({"message": "Winner updated successfully"})

