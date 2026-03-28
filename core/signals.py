from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match, Prediction


@receiver(post_save, sender=Match)
def update_prediction_points(sender, instance, **kwargs):

    if instance.winner and instance.winner != None:

        predictions = Prediction.objects.filter(match=instance)

        for prediction in predictions:

            if prediction.predicted_winner == instance.winner:
                prediction.points = 10
            else:
                prediction.points = 0

            prediction.save()