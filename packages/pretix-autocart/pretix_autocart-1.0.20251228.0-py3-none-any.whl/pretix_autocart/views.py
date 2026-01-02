import logging
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from pretix.base.settings import GlobalSettingsObject

logger = logging.getLogger(__name__)


@method_decorator(xframe_options_exempt, "dispatch")
class GetPubKeyView(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        gs = GlobalSettingsObject()
        return HttpResponse(gs.settings.feature_autocart_public_key, content_type="text/plain")
