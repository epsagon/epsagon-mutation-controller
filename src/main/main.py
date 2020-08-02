"""
Epsagon mutation controller
"""
import os
import copy
import base64
import argparse
import logging
import requests
import jsonpatch
from flask import Flask, request, jsonify

logging.getLogger().setLevel(logging.DEBUG)
app = Flask(__name__)

EPSAGON_MUTATTIONS_ENDPOINT = (
    'https://production.mutations.epsagon.com/production/mutation'
)
EPSAGON_MUTATION = "epsagon-mutation"
EPSAGON_MUTATION_CLUSTER = "epsagon-mutation-cluster"
EPSAGON_AUTO_INST_FLAG = "epsagon-auto-instrument"
ENABLE_INSTRUMENTATION = "enable"
DISABLE_INSTRUMENTATION = "disable"
TOKEN = os.getenv('EPSAGON_TOKEN', 'NONE')
app.config['EPSAGON_MUTATTIONS_ENDPOINT'] = os.getenv(
    'EPSAGON_MUTATTIONS_ENDPOINT', EPSAGON_MUTATTIONS_ENDPOINT)


@app.route("/")
def hello():
    """ hello from python """
    logging.info('info message')
    return "Hello from Python!"


@app.route("/healthz")
def healthz():
    """ healthz for readyness checks """
    return "OK", 200


def _get_mutation_cluster_annotation(request_data):
    """
    Gets the epsagon mutation cluster annotation value, None if not exists
    """
    if not request_data.json:
        return None
    try:
        return request_data.json['request']['oldObject']["metadata"][
            "annotations"][EPSAGON_MUTATION_CLUSTER]
    except KeyError:
        return None


def _is_reinstrumented_by_epsagon(deployment):
    """
    Checks whether given deployment has been changed by Epsagon
    """
    return (
        deployment['metadata']['labels'].get(EPSAGON_AUTO_INST_FLAG, "") == ENABLE_INSTRUMENTATION
    )


def _save_epsagon_instrumentation(deployment):
    """
    Keeps epsagon changes on mutated deployment
    """
    epsagon_data = {'epsagon_token': TOKEN}
    epsagon_data.update(request.json)
    if 'labels' not in deployment['metadata']:
        deployment['metadata']['labels'] = {}
    if not _is_reinstrumented_by_epsagon(deployment):
        requests.post(app.config['EPSAGON_MUTATTIONS_ENDPOINT'], json=epsagon_data)
    deployment['metadata']['labels'].pop(EPSAGON_AUTO_INST_FLAG, None)
    deployment['metadata']['labels'][EPSAGON_MUTATION] = 'enabled'
    mutation_cluster = _get_mutation_cluster_annotation(request)
    if mutation_cluster:
        if 'annotations' not in deployment:
            deployment['metadata']['annotations'] = {}
        deployment['metadata']['annotations'][
            EPSAGON_MUTATION_CLUSTER] = mutation_cluster


def _remove_epsagon_instrumentation(deployment):
    """
    Removes epsagon changes from mutated deployment
    """
    if "labels" in deployment['metadata']:
        deployment['metadata']['labels'].pop(EPSAGON_AUTO_INST_FLAG, None)
        deployment['metadata']['labels'].pop(EPSAGON_MUTATION, None)
    if "annotations" in deployment['metadata']:
        deployment['metadata']['annotations'].pop(EPSAGON_MUTATION_CLUSTER, None)


@app.route("/mutate", methods=['POST'])
def mutate():
    """
    Mutation admission main endpoint
    Sends epsagon a notification about the change and
    preserves the 'epsagon-mutatoin' label
    """
    try:
        deployment = request.json['request']['object']
        modified_deployment = copy.deepcopy(deployment)
        if (
                modified_deployment['metadata'].get("labels", {}).get(
                    EPSAGON_AUTO_INST_FLAG, ""
                ) == DISABLE_INSTRUMENTATION
        ):
            _remove_epsagon_instrumentation(modified_deployment)
        else:
            _save_epsagon_instrumentation(modified_deployment)
        patch = jsonpatch.JsonPatch.from_diff(deployment, modified_deployment)
    except Exception: # pylint: disable=broad-except
        patch = []

    admission_response = {
        'uid': request.json['request']['uid'],
        'allowed': True,
        'patchtype': 'JSONPatch',
        'result': {
            'status': 'Success',
        },
        'patch': base64.b64encode(str(patch).encode()).decode(),
    }
    return jsonify({
        'response': admission_response,
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Epsagon Mutation Controller')
    parser.add_argument('--port', dest='port', default=8443, type=int,
                        help='Webhook server port.')
    parser.add_argument('--tlsCertFile', dest='tlsCertFile',
                        default='/etc/webhook/certs/cert.pem', type=str,
                        help='File containing the x509 Certificate for HTTPS.')
    parser.add_argument('--tlsKeyFile', dest='tlsKeyFile',
                        default='/etc/webhook/certs/key.pem', type=str,
                        help=('File containing the x509 private key'
                              'to --tlsCertFile.'))

    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port,
            ssl_context=(args.tlsCertFile, args.tlsKeyFile))
