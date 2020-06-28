"""
Epsagon mutation controller
"""
import os
import copy
import base64
import argparse
import requests
import jsonpatch
from flask import Flask, request, jsonify
import logging

logging.getLogger().setLevel(logging.DEBUG)
app = Flask(__name__)


EPSAGON_MUTATTIONS_ENDPOINT = (
    'https://production.mutations.epsagon.com/production/mutation'
)
app.config['EPSAGON_MUTATTIONS_ENDPOINT'] = os.getenv(
    'EPSAGON_MUTATTIONS_ENDPOINT', EPSAGON_MUTATTIONS_ENDPOINT)


@app.route("/")
def hello():
    logging.info('info message')
    return "Hello from Python!"


@app.route("/healthz")
def healthz():
    return "OK", 200


@app.route("/mutate", methods=['POST'])
def mutate():
    requests.post(app.config['EPSAGON_MUTATTIONS_ENDPOINT'], json=request.json)

    deployment = request.json['request']['object']
    modified_deployment = copy.deepcopy(deployment)
    if 'labels' not in modified_deployment['metadata']:
        modified_deployment['metadata']['labels'] = {}
    modified_deployment['metadata']['labels']['epsagon-mutation'] = 'enabled'
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
