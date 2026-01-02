from django.urls import re_path

from .views import GetPubKeyView

urlpatterns = [
    re_path(r"^autocart/", GetPubKeyView.as_view(), name="pubkey")
]
