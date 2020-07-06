# pylint: disable=too-few-public-methods
"""
Test
"""
import json
from base64 import b64decode
from flask import url_for
from pytest_httpserver import HTTPServer
from main.main import app

app.config['EPSAGON_MUTATTIONS_ENDPOINT'] = (
    'http://localhost:5000/test/')


class TestHealthz:
    """ simple healthz test """
    @staticmethod
    def test_healthz():
        """ simple healthz test """
        with app.test_request_context():
            client = app.test_client()
            assert client.get(url_for('healthz')).status_code == 200


class TestMutate:
    """ test for the /mutate endpoint """
    @staticmethod
    def test_sanity():
        """ basic sanity test """
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
                                'epsagon-auto-instrument': 'test-auto-instrument'
                            },
                        },
                    },
                    'oldObject': {
                        'metadata': {
                            'annotations': {
                                'epsagon-mutation-cluster': "random_cluster",
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
            expected_patch = [
                {'op': 'add',
                 'path': '/metadata/labels/epsagon-mutation',
                 'value': 'enabled',
                 },
                {'op': 'add',
                 'path': '/metadata/annotations',
                 'value': {'epsagon-mutation-cluster': 'random_cluster'}
                 },
                {'op': 'remove',
                 'path': '/metadata/labels/epsagon-auto-instrument',
                },
            ]
            # patch changes order might change between tests
            assert len(expected_patch) == len(response_patch)
            for action in expected_patch:
                assert action in response_patch


    @staticmethod
    def test_with_label():
        """ test that if the labels exist it will be handled well """
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
                                'epsagon-mutation': 'enabled',
                            },
                            'annotations': {
                                'epsagon-mutation-cluster': "random_cluster",
                            },
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
