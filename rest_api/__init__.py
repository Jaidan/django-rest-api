import inspect
import json
from io import BytesIO
from django.core.handlers.wsgi import WSGIRequest
from django.utils import datastructures
from django.http import QueryDict
from django.http.response import HttpResponseBadRequest
from django.utils.datastructures import MultiValueDict


class MetaClass(type):
    def __new__(self, classname, classbases, classdict):
        try:
            frame = inspect.currentframe()
            frame = frame.f_back
            if frame.f_locals.has_key(classname):
                old_class = frame.f_locals.get(classname)
                for name, func in classdict.items():
                    #isdatadescriptor matches properties
                    if inspect.isfunction(func) or inspect.isdatadescriptor(func):
                        setattr(old_class, name, func)
                return old_class
            return type.__new__(self, classname, classbases, classdict)
        finally:
            del frame

class MetaObject(object):
    __metaclass__ = MetaClass

class WSGIRequest(MetaObject):
    def _set_put(self, put):
        self._put = put

    def _get_put(self):
        if not hasattr(self, '_put'):
            self._load_post_and_files()
        return self._put

    def _load_post_and_files(self):
        if self.method != 'POST' and self.method != 'PUT':
            query_data, self._files = QueryDict('', encoding=self._encoding), MultiValueDict()
            self._post = query_data
            self._put = query_data
            return
        if self._read_started and not hasattr(self, '_body'):
            self._mark_post_parse_error()
            return

        if hasattr(self, '_body'):
            # Use already read data
            data = BytesIO(self._body)
        else:
            data = self

        query_data = ''

        if self.META.get('CONTENT_TYPE', '').startswith('multipart/form-data'):
            try:
                query_data, self._files = self.parse_file_upload(self.META, data)
            except:
                # An error occured while parsing POST data. Since when
                # formatting the error the request handler might access
                # self.POST, set self._post and self._file to prevent
                # attempts to parse POST data again.
                # Mark that an error occured. This allows self.__repr__ to
                # be explicit about it instead of simply representing an
                # empty POST
                self._mark_post_parse_error()
                raise
        elif self.META.get('CONTENT_TYPE', '').startswith('application/x-www-form-urlencoded'):
            query_data, self._files = QueryDict(data, encoding=self._encoding), MultiValueDict()
        elif self.META.get('CONTENT_TYPE').startswith('application/json'):
            try:
                query_data = json.loads(data)
            except ValueError:
                return HttpResponseBadRequest(json.dumps({
                    '__all__': 'Malformed JSON'}))
        else:
            query_data, self._files = QueryDict('', encoding=self._encoding), MultiValueDict()
        self._post = {}
        self._put = {}
        setattr(self,
            '_%s' % self.method.lower(),
           query_data 
        )

    def _get_request(self):
        if not hasattr(self, '_request'):
            self._request = datastructures.MergeDict(self.POST, self.GET, self.PUT)
        return self._request

    REQUEST = property(_get_request)
    PUT = property(_get_put, _set_put)
