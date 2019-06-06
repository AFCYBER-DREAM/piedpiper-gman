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
        try:
            if isinstance(e, TypeError):
                return self.make_response({'message': f'{str(e)}'},
                                          400)
            if e.code == 404:
                try:
                    error = VarProxy.path_errors[0]
                    VarProxy.path_errors = []
                    return self.make_response({'message': f'404 Not Found: {str(error)}'},
                                              e.code)
                except IndexError:
                    return self.make_response({'message': str(e)}, e.code)
            elif e.code == 500:
                return self.make_response({'message': 'Internal Server Error'}, e.code)
            else:
                return self.make_response({'message': str(e)}, e.code)
        except AttributeError:
            return self.make_response({'message': f'Internal Server Error{str(e)}'},
                                      500)


class GManJSONEncoder(flask.json.JSONEncoder):

    def default(self, obj):
        """Add support for supported types"""
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
        if isinstance(value, str):
            return sri.hash_to_urlsafeb64(sri.sri_to_hash(value))
        if isinstance(value, integrity.Hash):
            return sri.hash_to_urlsafeb64(value)
        else:
            err = ValidationError(f'Must be of type {str(integrity.Hash)}')
            VarProxy.path_errors.append(err)
            raise err
