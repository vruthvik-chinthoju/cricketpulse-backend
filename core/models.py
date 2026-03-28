from django.db import models
from django.contrib.auth.models import User
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals

        

class Team(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Match(models.Model):
    match_number = models.IntegerField(unique=True)
    team1 = models.ForeignKey(Team,on_delete=models.CASCADE,related_name="team1_matches")
    team2 = models.ForeignKey(Team,on_delete=models.CASCADE,related_name="team2_matches")
    venue = models.CharField(max_length=100)
    match_date = models.DateTimeField()
    status = models.CharField(max_length=10,choices=[("upcoming", "Upcoming"),("live", "Live"),("completed", "Completed"),],default="upcoming")

    winner = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_matches",
    )

    def __str__(self):
        return f"Match {self.match_number}: {self.team1} vs {self.team2}"


class Prediction(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="predictions")
    match = models.ForeignKey(Match,on_delete=models.CASCADE,related_name="predictions")
    predicted_winner = models.ForeignKey(Team,on_delete=models.CASCADE)
    prediction_deadline = models.DateTimeField(blank=True, null=True)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("user", "match")



class CachedPlayer(models.Model):
    player_id = models.CharField(max_length=100, unique=True)
    data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)