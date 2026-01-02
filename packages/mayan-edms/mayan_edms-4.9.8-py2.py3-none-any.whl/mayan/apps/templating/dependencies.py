from mayan.apps.dependencies.classes import (
    JavaScriptDependency, PythonDependency
)

JavaScriptDependency(
    module=__name__, name='@highlightjs/cdn-assets', version_string='=11.9.0'
)

PythonDependency(
    module=__name__, name='django-mathfilters', version_string='==1.0.0'
)
