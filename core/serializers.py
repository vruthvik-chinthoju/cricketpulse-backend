from rest_framework import serializers
from .models import Match,Prediction,Team
from django.contrib.auth.models import User

class MatchSerializer(serializers.ModelSerializer):
    team1 = serializers.StringRelatedField()
    team2 = serializers.StringRelatedField()
    winner = serializers.StringRelatedField()

    team1_id = serializers.IntegerField(source="team1.id", read_only=True)
    team2_id = serializers.IntegerField(source="team2.id", read_only=True)


    class Meta:
        model = Match
        fields = "__all__"


class PredictionSerializer(serializers.ModelSerializer):
    match_number = serializers.IntegerField(source="match.match_number", read_only=True)
    team1 = serializers.StringRelatedField(source="match.team1", read_only=True)
    team2 = serializers.StringRelatedField(source="match.team2", read_only=True)

    predicted_team = serializers.StringRelatedField(source="predicted_winner", read_only=True)
    predicted_winner = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        write_only=True
    )

    match_date = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()

    class Meta:
        model = Prediction
        fields = [
            "id",
            "match",
            "match_number",
            "team1",
            "team2",
            "predicted_team",
            "predicted_winner",
            "match_date",
            "winner",
            "points",
            "created_at"
        ]

    def get_match_date(self, obj):
        return obj.match.match_date

    def get_winner(self, obj):
        return str(obj.match.winner) if obj.match.winner else None



class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user