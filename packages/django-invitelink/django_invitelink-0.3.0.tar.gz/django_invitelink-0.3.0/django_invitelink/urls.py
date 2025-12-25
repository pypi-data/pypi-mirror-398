from django.urls import path

from django_invitelink.views import Invite

urlpatterns = [
    path("invite/<uuid:invite>", Invite.as_view()),
]
