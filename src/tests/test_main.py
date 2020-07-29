# pylint: disable=too-few-public-methods
"""
Test
"""
import json
from base64 import b64decode
from flask import url_for
from pytest_httpserver import HTTPServer
from main.main import app
from main.main import (
    EPSAGON_MUTATION,
    EPSAGON_MUTATION_CLUSTER,
    EPSAGON_AUTO_INST_FLAG,
    EPSAGON_REMOVE_AUTO_INST_FLAG,
)

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
        with app.test_request_context():
            client = app.test_client()
            data = {
                'request': {
                    'uid': '123',
                    'object': {
                        'metadata': {
                            'labels': {
                                EPSAGON_AUTO_INST_FLAG: 'test-auto-instrument'
                            },
                        },
                    },
                    'oldObject': {
                        'metadata': {
                            'annotations': {
                                EPSAGON_MUTATION_CLUSTER: "random_cluster",
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
                 'path': f'/metadata/labels/{EPSAGON_MUTATION}',
                 'value': 'enabled',
                 },
                {'op': 'add',
                 'path': '/metadata/annotations',
                 'value': {EPSAGON_MUTATION_CLUSTER: 'random_cluster'}
                 },
                {'op': 'remove',
                 'path': f'/metadata/labels/{EPSAGON_AUTO_INST_FLAG}',
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
                                EPSAGON_MUTATION: 'enabled',
                            },
                            'annotations': {
                                EPSAGON_MUTATION_CLUSTER: "random_cluster",
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


    @staticmethod
    def test_removal():
        """ instrumentation removal test """
        with app.test_request_context():
            client = app.test_client()
            data = {
                'request': {
                    'uid': '123',
                    'object': {
                        'metadata': {
                            'labels': {
                                EPSAGON_REMOVE_AUTO_INST_FLAG: 'disable'
                            },
                        },
                    },
                    'oldObject': {
                        'metadata': {
                            'labels': {
                                EPSAGON_MUTATION: "enabled"
                            },
                            'annotations': {
                                EPSAGON_MUTATION_CLUSTER: "random_cluster",
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
                {'op': 'remove',
                 'path': f'/metadata/labels/{EPSAGON_REMOVE_AUTO_INST_FLAG}',
                },
            ]
            # patch changes order might change between tests
            assert len(expected_patch) == len(response_patch)
            for action in expected_patch:
                assert action in response_patch
