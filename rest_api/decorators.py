from oauth2app.authenticate import Authenticator
from functools import wraps
from django.utils.decorators import available_attrs
from oauth2app.models import AccessRange
from django.db.models.query import QuerySet

def oauth_validate(scope, authentication_class=Authenticator):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if not isinstance(scope, QuerySet):
                access_range = AccessRange.objects.filter(
                    key__in=scope)
            authenticator = authentication_class(scope=scope)
            try:
                authenticator.validate(request)
            except:
                return authenticator.error_response()
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
