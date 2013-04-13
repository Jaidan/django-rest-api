import logging
import json
from django.http import HttpResponse, Http404
from django.core.exceptions import ImproperlyConfigured
from django.views.generic import View
from django.views.generic.edit import ModelFormMixin, FormMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('django.request')

"""
API base generic classes
"""
class APIResponseMixin(object):
    """
    A mixin that can used to return an api response (JSON)
    TODO: Consider expanding to XML responses
    """

    def render_to_response(self, response_data, status_code=200):
        """
        Returns a response with the API data serialized
        """
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status=status_code
        )


class APIDataMixin(object):
    """
    A default mixin that accepts the keyword arguements recieved
    by get_data
    """
    
    def get_data(self, *args, **kwargs):
        return kwargs


class APIResponseView(APIResponseMixin, APIDataMixin, View):
    """
    A view that responds to an API request
    """
    extra_kwargs = {}

    def get(self, request, *args, **kwargs):
        if self.extra_kwargs:
            kwargs.update(self.extra_kwargs)
        data = self.get_data(**kwargs)
        return self.render_to_response(data)

class APIFormMixin(FormMixin):

    def form_invalid(self, form):
        logger.info(repr(form.errors))
        return self.render_to_response(form.errors, status_code=422)

    def form_valid(self, form):
        return self.render_to_response(form.get_data())

    def get_success_url(self):
        raise NotImplementedError

    def get_form_kwargs(self):
        """
        Returns the keyword arguements for instantiating the form
        """
        kwargs = { 'initial': self.get_initial() }
        if self.request.method == "POST":
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        elif self.request.method == "PUT":
            kwargs.update({
                'data': self.request.PUT,
                'files': self.request.FILES,
            })
        return kwargs

class APIModelFormMixin(ModelFormMixin, SingleObjectMixin):
    def form_invalid(self, form):
        logger.info(repr(form.errors))
        return self.render_to_response(form.errors, status_code=422)

    def form_valid(self, form, created=False):
        self.object = form.save()
        if created:
            status_code = 201
        else:
            status_code = 200
        return self.render_to_response(form.get_data(), status_code=status_code)

    def get_form_kwargs(self):
        """
        Returns the keyword arguements for instantiating the form
        """
        kwargs = { 'initial': self.get_initial() }
        if self.request.method == "POST":
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
                'instance': self.object,
            })
        elif self.request.method == "PUT":
            kwargs.update({
                'data': self.request.PUT,
                'files': self.request.FILES,
            })
        return kwargs

    def get_success_url(self):
        raise NotImplementedError


class APIPostView(APIResponseMixin, APIDataMixin, APIFormMixin, View):
    """
    A view that responds to a API POST request
    """

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

class APIDeleteView(APIResponseMixin, SingleObjectMixin):

    def delete(self, request, *args, **kwargs):
        try: 
            self.object = self.get_object()
            self.object.delete()
        except:
            return self.render_to_response({
                'success': False,
                'id': self.object.id,
            })
        else:
            return self.render_to_response({
                'success': True,
                'id': self.object.id,
            })


class APIUpdateView(APIResponseMixin, APIDataMixin, APIModelFormMixin, View):
    """
    A view that responds to a API POST request
    """

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

class APIPutView(APIResponseMixin, APIDataMixin, APIModelFormMixin, View):
    """
    A view that responds to a API PUT request
    """

    def put(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class APIReadView(APIResponseMixin, APIDataMixin, SingleObjectMixin):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = self.get_data(object=self.object)
        return self.render_to_response(data)

    def get_data(self, *args, **kwargs):
        obj= kwargs.pop('object')
        if obj and hasattr(obj, 'to_dict'):
            return obj.to_dict()


class APIMultipleObjectMixin(MultipleObjectMixin):
    """
    A mixin for views manipulating multiple objects
    """

    def get_date_filter_field(self):
        if self.date_filter_field is not None:
            return self.date_filter_field
        else:
            raise ImproperlyConfigured("'%s' must define a date_filter_field to use date filter" % self.__class__.__name__)

    def get_data(self, *args, **kwargs):
        queryset = kwargs.pop('object_list')
        page_size = self.get_paginate_by(queryset) 
        context_object_name = self.get_context_object_name(queryset)
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                queryset, page_size)
        data = [obj.to_dict() for obj in queryset]
        if kwargs:
            data = dict(
                {
                    context_object_name or 'object_list': data,
                }.items() + kwargs.items()
            )
        return data

class APIListView(APIMultipleObjectMixin, APIResponseView):
    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty:
            if (self.get_paginate_by(self.object_list) is not None
                and hasattr(self.object_list, 'exists')):
                is_empty = not self.object_list.exists()
            else:
                is_empty = len(self.object_list) == 0
            if is_empty:
                raise Http404(
                    "Empty list and '%(class_name)s.allow_empty is False." % {
                        'class_name': self.__class__.__name__ 
                    })
        data = self.get_data(object_list=self.object_list, **kwargs)
        return self.render_to_response(data)

    def get_data(self, *args, **kwargs):
        queryset = kwargs.pop('object_list')
        params = kwargs.pop('params', None)
        page_size = self.get_paginate_by(queryset) 
        context_object_name = self.get_context_object_name(queryset)
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                queryset, page_size)
        data = [obj.to_dict() for obj in queryset]
        if params:
            kwargs['params'] = params
            data = dict(
                {
                    context_object_name or 'object_list': data,
                }.items() + kwargs.items()
            )
        return data

"""
Concrete View Classes
"""
class APIListCreateView(APIListView, APIPutView):

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(APIListCreateView, self).dispatch(*args, **kwargs)

class APIReadUpdateDeleteView(APIReadView, APIUpdateView, APIDeleteView):
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(APIReadUpdateDeleteView, self).dispatch(*args, **kwargs)

class APIPutFileView(APIPutView):
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(APIPutFileView, self).dispatch(*args, **kwargs)
