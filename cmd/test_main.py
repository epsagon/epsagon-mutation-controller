"""
Test
"""
import json
from main import app
from flask import url_for
from base64 import b64decode
from pytest_httpserver import HTTPServer

app.config['EPSAGON_MUTATTIONS_ENDPOINT'] = (
    'http://localhost:5000/test/')


class TestHealthz:
    def test_healthz(self):
        with app.test_request_context():
            client = app.test_client()
            assert client.get(url_for('healthz')).status_code == 200


class TestMutate:
    def test_sanity(self):
        with app.test_request_context(), HTTPServer(port=5000) as httpserver:
            httpserver.expect_request('/test/', method='POST',
                                      ).respond_with_json({})
            client = app.test_client()
            data = {
                'request': {
                    'uid': '123',
                    'object': {
                        'metadata': {}
                    },
                },
            }
            res = client.post(url_for('mutate'), json=data)
            assert res.status_code == 200
            response_patch = json.loads(
                b64decode(
                    json.loads(
                        res.data.decode('utf-8'))[
                            'response']['patch']).decode('utf-8'))
            expected_patch = [
                {'op': 'add',
                 'path': '/metadata/labels',
                 'value': {'epsagon-mutation': 'enabled'}
                 }
            ]
            assert response_patch == expected_patch

    def test_with_label(self):
        with app.test_request_context(), HTTPServer(port=5000) as httpserver:
            httpserver.expect_request('/test/', method='POST',
                                      ).respond_with_json({})
            client = app.test_client()
            data = {
                'request': {
                    'uid': '123',
                    'object': {
                        'metadata': {
                            'labels': {
                                'epsagon-mutation': 'enabled'
                            }
                        }
                    },
                },
            }
            res = client.post(url_for('mutate'), json=data)
            assert res.status_code == 200
            response_patch = json.loads(
                b64decode(
                    json.loads(
                        res.data.decode('utf-8'))[
                            'response']['patch']).decode('utf-8'))
            expected_patch = []
            assert response_patch == expected_patch
