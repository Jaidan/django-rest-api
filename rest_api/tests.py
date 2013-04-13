import mock
from mock import Mock
import json
from django.test import TestCase
from middleware import APIParseRequestMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.test import Client

class JSONResponseTestCase(TestCase):
    def decode_response(self, response):
        return json.loads(response)


class APIParseMiddlewareTest(TestCase):
    def setUp(self):
        self.middleware = APIParseRequestMiddleware()
        self.data = {
            'foo': 'Hello World',
        }
        self.request = Mock()
        self.request.META = {}
        self.request.META['CONTENT_TYPE'] = 'application/json'
        self.request.method = ''
        self.request.body = ''

    def test_post(self):
        self.request.method = "POST"
        self.request.body = json.dumps(self.data)
        self.middleware.process_request(self.request)
        self.assertEqual(self.data, self.request.POST)

    def test_put(self):
        self.request.method = "PUT"
        self.request.body = json.dumps(self.data)
        self.middleware.process_request(self.request)
        self.assertEqual(self.data, self.request.PUT)

    def test_empty_get(self):
        self.request.method = "GET"
        # Simulate url querystring
        qs = { 'format': 'json' }
        self.request.GET = qs
        self.request.body = None
        self.middleware.process_request(self.request)
        self.assertEqual(qs, self.request.GET)

    def test_get(self):
        self.request.method = "GET"
        # Simulate url querystring
        qs = { 'format': 'json' }
        self.data.update(qs)
        self.request.GET = qs
        self.request.body = json.dumps(self.data)
        self.middleware.process_request(self.request)
        self.assertEqual(self.data, self.request.GET)

    def test_send_improper_json(self):
        self.request.method = "POST"
        self.request.body = """{
        name: 'Foo',
        phone: '1234587890',
        address: '123 abc st',
        city: 'ataset',
        state_province: 'adfadf',
        country: 'adfasdf',
        contact_first_name: 'adfadf',
        contact_last_name: 'adfadsf'
        contact_email: 'goo@goo.com',
        contact_phone: '1234587890'
        }"""
        response = self.middleware.process_request(self.request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            '__all__': 'Malformed JSON'})
