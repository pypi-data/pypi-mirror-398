from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig


class PlatformGitlabApp(MayanAppConfig):
    app_namespace = 'platform_gitlab'
    app_url = 'platform_gitlab'
    name = 'mayan.apps.platform_gitlab'
    verbose_name = _(message='Platform GitLab')
