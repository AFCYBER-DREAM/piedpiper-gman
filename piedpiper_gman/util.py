import uuid

import flask

import flask_restful

import subresource_integrity as integrity

from piedpiper import sri

from werkzeug.routing import (BaseConverter, ValidationError)


class VarProxy(object):

    path_errors = []


class Api(flask_restful.Api):

    def handle_error(self, e):
        if e.code == 404:
            try:
                error = VarProxy.path_errors[0]
                VarProxy.path_errors = []
                return self.make_response({'errors': [f'404 Not Found: {str(error)}']},
                                          e.code)
            except IndexError:
                return self.make_response({'errors': [str(e)]}, e.code)
        elif e.code == 500:
            return self.make_response({'errors': 'Internal Server Error'}, e.code)


class GManJSONEncoder(flask.json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, integrity.Hash):
            return str(obj)
        else:
            return super(GManJSONEncoder, self).default(obj)


class SRIConverter(BaseConverter):

    def to_python(self, value):
        try:
            return sri.urlsafe_to_hash(value)
        except Exception:
            err = ValidationError('Bad SRI Hash: make sure to python->'
                                  'base64.urlsafe_b64encode your sri hash')
            VarProxy.path_errors.append(err)
            raise err

    def to_url(self, value):
        if isinstance(value, integrity.Hash):
            return str(value)
        else:
            err = ValidationError(f'Must be of type {type(integrity.Hash)}')
            VarProxy.append(err)
            raise err
