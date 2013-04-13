import mock
from mock import Mock
import json
from django.test import TestCase
from django.core.handlers.wsgi import WSGIRequest
from django.test import Client

class JSONResponseTestCase(TestCase):
    def decode_response(self, response):
        return json.loads(response)

