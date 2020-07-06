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
            "annotations"]["epsagon-mutation-cluster"]
    except KeyError:
        return None


@app.route("/mutate", methods=['POST'])
def mutate():
    """
    Mutation admission main endpoint
    Sends epsagon a notification about the change and
    preserves the 'epsagon-mutatoin' label
    """
    epsagon_data = {'epsagon_token': TOKEN}
    epsagon_data.update(request.json)
    deployment = request.json['request']['object']
    modified_deployment = copy.deepcopy(deployment)

    if 'labels' not in modified_deployment['metadata']:
        modified_deployment['metadata']['labels'] = {}

    if "epsagon-auto-instrument" not in modified_deployment['metadata']['labels']:
        requests.post(app.config['EPSAGON_MUTATTIONS_ENDPOINT'], json=epsagon_data)
    else:
        modified_deployment['metadata']['labels'].pop("epsagon-auto-instrument")

    modified_deployment['metadata']['labels']['epsagon-mutation'] = 'enabled'
    mutation_cluster = _get_mutation_cluster_annotation(request)
    if mutation_cluster:
        if 'annotations' not in modified_deployment:
            modified_deployment['metadata']['annotations'] = {}
        modified_deployment['metadata']['annotations'][
            'epsagon-mutation-cluster'] = mutation_cluster
    patch = jsonpatch.JsonPatch.from_diff(deployment, modified_deployment)

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
