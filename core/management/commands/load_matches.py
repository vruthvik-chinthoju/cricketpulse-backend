import json
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import Match, Team


class Command(BaseCommand):
    help = "Load matches from JSON"

    def handle(self, *args, **kwargs):

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
                defaults={
                    "team1": team1,
                    "team2": team2,
                    "venue": m["venue"],
                    "match_date": match_datetime
                }
            )

        self.stdout.write(self.style.SUCCESS("Matches inserted successfully!"))