# django_invitelink

(formerly known as `apis_acdhch_django_invite`)

Invite app for Django applications.

This app provides an invite link that only works with valid tokens. The invite tokens can be generated in Django's admin interface.
The invite endpoint is `/invite/<token>`.

# Installation

Add `django_invitelink` to your `INSTALLED_APPS`.
Include the `django_invitelink.urls` in your `urls.py`:
```
urlpatterns += [path("", include("django_invitelink.urls")),]
```
