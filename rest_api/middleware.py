import json
from io import BytesIO
from django.http import HttpResponseBadRequest

class APIParseRequestMiddleware(object):
    """
    A middleware to parse PUT requests in the same way as a POST request
    This is kinda a kludge, it would be "better" to create a new request class
    that overrides some behavior from http.HttpReqest and is used by a subclass
    of handlers.WSGIHandler, but that is more than we need right now
    """
    def process_request(self, request):
        if request.META.get('CONTENT_TYPE') == 'application/json':
            # Kludge to work around a django bug.  Django munges the
            # request.POST when request.FILES is accessed for the first
            # time.  We access it here first so that when we write our own
            # request.POST into place we can't accidently destroy it by
            # checking for files later.  Possibly fixed in django 1.5 
            # Verify by checking a post request, no unit test available to
            # to test this behavior
            request.FILES
            if request.body:
                try:
                    request_json = json.loads(request.body)
                except ValueError:
                    return HttpResponseBadRequest(json.dumps({
                        '__all__': 'Malformed JSON'}))
                setattr(request,
                    request.method.upper(),
                    request_json
                )
        elif request.method == 'PUT':
            qd, files = request.parse_file_upload(
                request.META,
                BytesIO(request.body),
            )
            request.PUT = qd
            request._post = qd
            request._files = files
