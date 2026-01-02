from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_autocart"
    verbose_name = "pretix_auto_cart_questions"

    class PretixPluginMeta:
        name = gettext_lazy("Pretix auto cart&questions")
        author = "Furizon Team"
        description = gettext_lazy("Enables autocompletition of pretix's carts and questions using the URL")
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA
