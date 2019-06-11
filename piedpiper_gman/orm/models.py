import uuid

from marshmallow_peewee import ModelSchema, Related

from peewee import (DatabaseProxy,
                    DateTimeField,
                    ForeignKeyField,
                    Model,
                    SqliteDatabase,
                    TextField)

db = DatabaseProxy()


class Task(Model):
    task_id = TextField(primary_key=True, default=uuid.uuid4)
    run_id = TextField(null=False)
    project = TextField(null=False)
    caller = TextField(null=False)
    thread_id = TextField(null=True)

    class Meta:
        database = db


class TaskEvent(Model):
    task = ForeignKeyField(Task)
    timestamp = DateTimeField()
    status = TextField(null=False, choices=(('started', 'started'),
                                            ('completed', 'completed'),
                                            ('failed', 'failed'),
                                            ('delegated', 'delegated'),
                                            ('received', 'received'),
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
    db.create_tables([Task, TaskEvent], safe=True)
