#!/usr/bin/env python3
from os.path import abspath
from os.path import expanduser
import argparse
import json
import os
import sys

from marshmallow import Schema
from marshmallow import ValidationError
from libsousou.web import RequestController
from libsousou.web import IRequest
from libsousou.web.exc import BadRequest
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response
from werkzeug.contrib.wrappers import JSONRequestMixin
import marshmallow.fields
import ioc

from gateway.dto import CommandRequestDTO


parser = argparse.ArgumentParser("Launches the Gateway HTTP interface.")
parser.add_argument('--debug', action='store_true',
    help="Enabled debug mode (default: false)")
parser.add_argument('--ioc', type=lambda x: abspath(expanduser(x)),
    default='/etc/gateway/gateway.ioc',
    help="Specifies the location to the Inversion-of-Control configuration file.")
args = parser.parse_args()

TOKEN_PARAM = 'token'
IOC_CONFIG=os.getenv('GATEWAY_IOC_CONFIG') or args.ioc
if not os.path.exists(IOC_CONFIG):
    print("No such file: " + IOC_CONFIG)
    sys.exit(1)

ioc.load_container(IOC_CONFIG)

DEBUG = bool('GATEWAY_DEBUG') or args.debug
HOST = os.getenv('GATEWAY_HOST','127.0.0.1')
try:
    PORT = int(os.getenv('GATEWAY_PORT', 4210))
except ValueError:
    print("Invalid value set for GATEWAY_PORT")
    sys.exit(1)




class GatewayController(RequestController):
    default_content_type = "application/json"
    disable_authentication = True
    gateway = ioc.instance('CommandGateway')
    auth_service = ioc.instance('AuthenticationService')
    response_class = Response
    debug = '--debug' in sys.argv
    CommandParsingError = ValidationError

    def __init__(self, *args, **kwargs):
        self.command_schema = self.CommandRequestSchema()
        super(GatewayController, self).__init__(*args, **kwargs)

    def response_factory(self, *args, **kwargs):
        kwargs['status'] = kwargs.pop('status_code', None) or kwargs.get('status')
        return self.response_class(*args, **kwargs)

    def render(self, context):
        return json.dumps(context, indent=4)

    def get(self, request, **kwargs):
        return self.render_to_response(self.gateway.get_commands())

    def post(self, request, **kwargs):
        try:
            command = self.parse_command(request)
            result = \
                self.gateway.issue(command)
            status = 200
            if result.created:
                status = 201
            if not result.done:
                status = 202

            result = {
                'command_id': result.command_id,
                'ident': result.ident,
                'result': result.result
            }
        except self.gateway.CommandFailed as e:
            status = 500
            result = {
                'code': 'FATAL_ERROR',
                'message': "Fatal error during command handling.",
                'hint': e.reason
            }
        except self.gateway.NotAuthorized:
            status = 401
            result = {
                'code': 'AUTHORIZATION_FAILURE',
                'message': "You are not authorized to issue this command.",
                'hint': e.reason
            }
        except self.gateway.DuplicateEntity as e:
            status = 409
            result = {
                'code': 'DUPLICATE_ENTITY',
                'message': "The issued command causes a conflicting state.",
                'hint': e.reason
            }
        except (self.gateway.CommandRejected, self.CommandParsingError) as e:
            status = 422
            result = {
                'code': 'UNPROCESSABLE_ENTITY',
                'message': "The command provided in the request could not be processed.",
                'hint': getattr(e, 'reason', "Invalid command parameters."),
                'context': getattr(e, 'context', {})
            }
        except self.gateway.ReadOnlyMode as e:
            status = 503
            result = {
                'code': 'READONLY_MODE',
                'message': "The system is in read-only mode.",
                'hint': e.reason or "The system is in read-only mode until further notice."
            }
        except self.gateway.UpstreamFailure as e:
            status = 503
            result = {
                'code': 'UPSTREAM_FAILURE',
                'message': "An upstream system component failed to service.",
                'hint': e.reason
            }
        return self.render_to_response(result, status=status)

    def parse_command(self, request):
        data = request.json
        data.update({
            'issuer': request.issuer,
            'authenticated_by': request.authenticated_by,
            'host': request.remote_addr
        })
        command, errors = self.command_schema.load(data)
        if errors:
            raise self.UnprocessableEntity({'hint': "Malformed command request."})

        return command

    class CommandRequestSchema(Schema):
        command = marshmallow.fields.String(required=True)
        params = marshmallow.fields.Dict(required=True)
        asynchronous = marshmallow.fields.Boolean(default=False, missing=False)
        host = marshmallow.fields.String(required=True)
        issuer = marshmallow.fields.Integer(required=True)
        authenticated_by = marshmallow.fields.Integer(required=True)

        @marshmallow.decorators.post_load
        def create_dto(self, data):
            # The id attribute will be set by the command storage backend.
            data['id'] = None
            return CommandRequestDTO(**data)


class GatewayApplication:
    urls = Map([
        Rule('/v1/command', methods=['POST','GET'], endpoint='command')
    ])

    endpoints = {
        'command': GatewayController.as_view(),
    }
    response_class = Response

    def __init__(self, ioc_config=None, debug=False):
        self.ioc_config = ioc_config
        self.debug = debug

    def __call__(self, environ, start_response):
        response = self.process_request(self.request_class(environ))
        return response(environ, start_response)

    def process_request(self, request):
        adapter = self.urls.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            response = self.invoke_handler(request, endpoint, values)
        except HTTPException as e:
            response = self.response_class("", content_type="application/json", status=e.code)

        return response

    def invoke_handler(self, request, endpoint, values):
        handler = self.endpoints[endpoint]
        return handler(request, **values)

    class request_class(Request, IRequest):
        issuer = 100
        authenticated_by = 100

        @property
        def json(self):
            try:
                data = json.loads(self.data.decode("utf-8"))
            except Exception:
                raise BadRequest
            return data

        def get_request_method(self):
            return self.method


application = GatewayApplication(
    ioc_config=IOC_CONFIG,
    debug=DEBUG
)
if __name__ == '__main__':

    run_simple(HOST, PORT, application,
        use_reloader=DEBUG,
        use_debugger=DEBUG
    )
