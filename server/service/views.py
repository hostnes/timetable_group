from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from service.models import User
from service.serializers import UserSerializers


@api_view(["GET"])
def health_check(request):
    return Response({"status": "Ok"}, status.HTTP_200_OK)


class UserRetrieve(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializers


class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializers
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['first_name', 'telegram_id', 'group_number']


def week(requests):
    return render(requests, 'week.html')