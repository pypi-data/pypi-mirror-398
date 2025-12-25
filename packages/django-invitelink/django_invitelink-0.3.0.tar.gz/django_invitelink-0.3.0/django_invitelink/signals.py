from django.db.models.signals import ModelSignal

consume_invite = ModelSignal(use_caching=True)
