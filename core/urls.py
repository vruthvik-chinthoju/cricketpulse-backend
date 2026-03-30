from django.urls import path
from .views import match_list, create_prediction, my_predictions, leaderboard,register_view,team_list,current_user,get_ipl_squads,get_player_info,predict_match,chat_ai,update_match_winner

urlpatterns = [
    path('matches/', match_list),
    path('predict/', create_prediction),
    path('my-predictions/', my_predictions),
    path('leaderboard/', leaderboard),
    path('register/', register_view),
    path('teams/', team_list),
    path('api/user/', current_user),
    path('ipl/teams/<str:year>/',get_ipl_squads),
    path('ipl/player/<str:player_id>/', get_player_info),
    path("predict/<int:match_id>/",predict_match),
    path("chat-ai/", chat_ai),
    path("update-winner/<int:match_id>/",update_match_winner),
    
    
]