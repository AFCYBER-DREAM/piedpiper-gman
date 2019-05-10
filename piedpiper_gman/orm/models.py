import os
import uuid

from marshmallow_peewee import ModelSchema, Related
from piedpiper_gman.config import Config
from peewee import *

# gman schema: task_id(guid), timestamp(datetime), status[started, completed, failed, info], caller, message(text), run_id(guid)

if Config.database.type == 'sqlite':
    db = SqliteDatabase(Config.database.uri, pragmas={'foreign_keys': 1})
else:
    raise Exception(f'Database type {config.database.type} not yet supported')


class Task(Model):
    task_id = TextField(primary_key=True, default=uuid.uuid4)
    run_id = TextField(null=False)
    project = TextField(null=True)
    caller = TextField(null=False)

    class Meta:
        database = db


class TaskEvent(Model):
    task = ForeignKeyField(Task)
    timestamp = DateTimeField()
    status = TextField(null=False, choices=(('started', 'started'),
                                            ('completed', 'completed'),
                                            ('failed', 'failed'),
                                            ('info', 'info')))
    message = TextField(null=False)

    class Meta:
        database = db


class TaskSchema(ModelSchema):

    class Meta:
        model = Task


class TaskEventSchema(ModelSchema):

    task = Related()

    class Meta:
        model = TaskEvent


def db_init():
    db.connect()
    db.create_tables([Task, TaskEvent], safe=True)
