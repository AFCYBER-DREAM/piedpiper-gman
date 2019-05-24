import uuid

import flask


class GManJSONEncoder(flask.json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, uuid.UUID):
            return str(obj)
        else:
            return super(GManJSONEncoder, self).default(obj)
