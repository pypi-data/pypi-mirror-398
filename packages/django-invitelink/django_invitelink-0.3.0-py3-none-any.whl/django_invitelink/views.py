from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404
from django.views.generic.edit import CreateView

from django_invitelink.models import InviteToken
from django_invitelink.signals import consume_invite


class Invite(CreateView):
    form_class = UserCreationForm
    template_name = "invite.html"
    success_url = settings.LOGIN_URL

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.invite = get_object_or_404(InviteToken, id=kwargs.get("invite"))

    def form_valid(self, form):
        ret = super().form_valid(form)
        self.invite.delete()
        consume_invite.send(sender=self.object)
        messages.success(self.request, f"Created user {self.object}")
        return ret
