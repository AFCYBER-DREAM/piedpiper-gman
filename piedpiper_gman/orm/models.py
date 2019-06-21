import uuid
from urllib.parse import urlparse, urlunparse, ParseResult

from marshmallow import fields as marshmallow_fields

from marshmallow_peewee import ModelSchema, Related
from marshmallow_peewee.convert import ModelConverter

from peewee import (DatabaseProxy,
                    DateTimeField,
                    ForeignKeyField,
                    IntegerField,
                    Model,
                    DoesNotExist,
                    SqliteDatabase,
                    TextField)

import subresource_integrity as integrity

db = DatabaseProxy()


class ZeroResults(DoesNotExist):

    pass


class QueryFailed(Exception):

    pass


class SRIField(TextField):
    '''A field type that stores an HTML SRI value
    Value must be of from hash: hashvalue.
    '''

    def db_value(self, value):
        if isinstance(value, integrity.Hash):
            return str(value)
        else:
            try:
                return str(integrity.parse(value)[0])
            except IndexError:
                raise ValueError('This does not appear to be of type "Hash" or "str"')

    def python_value(self, value):
        return integrity.parse(value)[0]


class URIField(TextField):

    def db_value(self, value):

        if isinstance(value, ParseResult):
            return urlunparse(value)
        elif isinstance(value, str):
            return urlunparse(urlparse(value))
        else:
            raise ValueError(f'Non urlparse parseable type {type(value)}')

    def python_value(self, value):

        if isinstance(value, ParseResult):
            return value
        elif isinstance(value, str):
            return urlparse(value)
        else:
            raise ValueError(f'Non urlparse parseable type {type(value)}')

    def _serialize(self, value, attr, obj, **kwargs):
        return urlunparse(value)

    def _deserialize(self, value, attr, data, **kwargs):
        return urlparse(value)


class Task(Model):
    task_id = TextField(primary_key=True, default=uuid.uuid4)
    run_id = TextField(null=False)
    project = TextField(null=False)
    caller = TextField(null=False)
    thread_id = TextField(null=True)

    class Meta:
        database = db


class TaskEvent(Model):
    event_id = TextField(primary_key=True, default=uuid.uuid4)
    task = ForeignKeyField(Task)
    timestamp = DateTimeField()
    status = TextField(null=False, choices=(('started', 'started'),
                                            ('completed', 'completed'),
                                            ('failed', 'failed'),
                                            ('delegated', 'delegated'),
                                            ('received', 'received'),
                                            ('info', 'info')))
    message = TextField(null=False)
    return_code = IntegerField(null=True)

    class Meta:
        database = db


class ExtendedConverter(ModelConverter):

    def __new__(cls, **kwargs):

        cls.TYPE_MAPPING.append((URIField, marshmallow_fields.String))
        return ModelConverter.__new__(cls)

    def convert_field(self, field, **kwargs):

        converted = super(ExtendedConverter, self).convert_field(field, **kwargs)

        if hasattr(field, '_deserialize'):
            converted._deserialize = field._deserialize

        if hasattr(field, '_serialize'):
            converted._serialize = field._serialize

        return converted


class TaskSchema(ModelSchema):

    class Meta:
        model = Task


class TaskEventSchema(ModelSchema):

    task = Related()

    class Meta:
        model = TaskEvent


class Artifact(Model):
    artifact_id = TextField(primary_key=True, default=uuid.uuid4)
    uri = URIField(null=False)
    sri = SRIField(null=False)
    status = TextField(null=False, choices=(('unique', 'unique'),
                                            ('collision', 'collision'),
                                            ('deleted', 'deleted'),
                                            ('unknown', 'unknown')))
    type = TextField(null=False, choices=(('log', 'log'),
                                          ('container', 'container'),
                                          ('artifact', 'artifact'),
                                          ('source', 'source')))

    task = ForeignKeyField(Task)
    event_id = ForeignKeyField(TaskEvent)

    class Meta:
        database = db


class ArtifactSchema(ModelSchema):

    task = Related()

    class Meta:
        model = Artifact
        model_converter = ExtendedConverter


def db_init(db_config):

    if db_config.type == 'sqlite':
        db_run = SqliteDatabase(db_config.uri,
                                pragmas={'foreign_keys': 1})
    else:
        raise Exception(f'Database type {db_config.type}'
                        ' not yet supported')

    # Configure our proxy to use the db we specified in config.
    db.initialize(db_run)

    db.connect()
    db.create_tables([Task, TaskEvent, Artifact], safe=True)
