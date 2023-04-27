from django.urls import path, include

from .views import health_check, UserList, UserRetrieve, week

urlpatterns = [
    path('ping/', health_check),

    path('users/', UserList.as_view()),
    path('user/<int:pk>/', UserRetrieve.as_view()),

    path('week/', week),
]