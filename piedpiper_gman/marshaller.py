from attrdict import AttrDict


class MarshalError(Exception):

    def __init__(self, errors):
        self.errors = errors


class Errors(object):

    def __init__(self):
        self.errors = {}
        self.errors_data = {}

    def add(self, key, error, data=None):
        if data:
            self.errors_data[key] = data
        self.errors.setdefault(key, []).append(error)

    def extend(self, errors, data=None):
        assert isinstance(errors, dict)
        if data:
            self.errors_data['bulk'] = data
        for key, errs in errors.items():
            if key in self.errors:
                self.errors[key].extend(errs)
            else:
                self.errors[key] = errs

    def emit(self):
        return {'errors': self.errors}


class Marshaller(object):

    def __init__(self, raw):
        assert isinstance(raw, dict)
        self.errors = Errors()
        self.raw_data = AttrDict(raw)
