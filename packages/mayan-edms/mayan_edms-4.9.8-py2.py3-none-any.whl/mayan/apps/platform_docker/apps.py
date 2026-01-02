from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig


class PlatformDockerApp(MayanAppConfig):
    app_namespace = 'platform_docker'
    app_url = 'platform_docker'
    name = 'mayan.apps.platform_docker'
    verbose_name = _(message='Platform Docker')
