import datetime
import re

from attrdict import AttrDict

from flask import request
from flask_restful import Resource
from peewee import DoesNotExist
from piedpiper_gman.orm.models import (Task,
                                       TaskEvent,
                                       TaskSchema,
                                       TaskEventSchema)


class Errors(object):

    def __init__(self):
        self.errors = {}

    def add(self, key, error):
        self.errors.setdefault(key, []).append(error)

    def extend(self, errors):
        for key, errs in errors.items():
            if key in self.errors:
                self.errors[key].extend(errs)
            else:
                self.errors[key] = errs

    def emit(self):
        return {'errors': self.errors}


class MarshalError(Exception):

    def __init__(self, errors):
        self.errors = errors


class GManMarshaller(object):

    def __init__(self, raw):
        assert isinstance(raw, dict)
        self.errors = Errors()
        self.raw_data = AttrDict(raw)

        self._task = None
        self._event = None

    def enforce(self, context):

        self._task = TaskSchema().load(self.raw_data)
        self._event = TaskEventSchema().load(self.raw_data, partial=('timestamp',))

        try:
            self._event.data.timestamp = datetime.datetime.now()
        except AttributeError:
            self._event.data['timestamp'] = datetime.datetime.now()

        if self._task.errors:
            self.errors.extend(self._task.errors)

        if self._event.errors:
            self.errors.extend(self._event.errors)

        if context == 'create_task':
            disallowed = ('task_id', 'timestamp')

            if self.raw_data['status'] not in ('started', 'received'):
                self.errors.add('status',
                                'Task creation must be \'started\' or \'received\'')
            else:
                if (self.raw_data['status'] == 'received'
                        and not len(self.raw_data['thread_id'])):
                    self.errors.add('thread_id',
                                    'Thread_id is required for status received')

        elif context == 'add_event':
            disallowed = ('caller', 'thread_id', 'timestamp', 'project', 'run_id')
            if self.raw_data.get('status', '') in ('started', 'received'):
                self.errors.add('status', 'Updates may not be value \'started\'')

        for key in disallowed:
            if key in self.raw_data:
                self.errors.add(key, 'May not be specified on a post/create')

        if len(self.errors.errors):
            raise MarshalError(self.errors)

    @property
    def task(self):
        return self._task

    @property
    def event(self):
        return self._event


class GMan(Resource):

    def get(self, task_id, events=None):

        try:
            task = Task.get(Task.task_id == task_id)
        except DoesNotExist:
            return {'message': 'Not Found'}, 404

        if events:
            events = [x for x in
                      TaskEvent.select()
                               .join(Task)
                               .where(Task.task_id == task_id)
                               .order_by(TaskEvent.timestamp)]

            if len(events):
                return TaskEventSchema(many=True, exclude=['id']).dump(events).data
            else:
                return {'message': 'Not Found'}, 404

        else:
            return TaskSchema().dump(task)

    def put(self, task_id, events=None, json=None):

        if events:
            return {'message': 'Not Found'}, 404

        if json:
            raw = json
        else:
            raw = request.get_json(force=True)

        marshaller = GManMarshaller(raw)

        try:
            marshaller.enforce('add_event')
            task = Task.get(Task.task_id == task_id)

            event = TaskEvent.create(task=task,
                                     message=marshaller.event.message,
                                     status=marshaller.event.status,
                                     timestamp=marshaller.event.timestamp)

            return TaskEventSchema(exclude=['id']).dump(event)

        except MarshalError as e:
            return e.errors.emit(), 422
        except DoesNotExist:
            return {'message': 'Not Found'}, 404

    def post(self, *args, **kwargs):
        if 'task_id' in kwargs or 'events' in kwargs:
            return {'message': 'Unprocessable request'}, 422

        if 'json' in kwargs:
            raw = kwargs['json']
        else:
            raw = request.get_json(force=True)

        marshaller = GManMarshaller(raw)
        try:
            marshaller.enforce('create_task')
            if marshaller.task.data.thread_id:
                Task.get(Task.task_id == marshaller.task.data.thread_id)

            task = Task.create(task_id=marshaller.task.data.task_id,
                               run_id=marshaller.task.data.run_id,
                               project=marshaller.task.data.project,
                               thread_id=marshaller.task.data.thread_id,
                               caller=marshaller.task.data.caller)

            event = TaskEvent.create(task=task,
                                     message=marshaller.event.data.message,
                                     status=marshaller.event.data.status,
                                     timestamp=marshaller.event.data.timestamp)

            return TaskEventSchema(exclude=['id']).dump(event)

        except MarshalError as e:
            return e.errors.emit(), 422
        except DoesNotExist:
            marshaller.errors.add('thread_id',
                                  'thread_id must be an existing task_id')
            return marshaller.errors.emit(), 422
        except AttributeError as e:
            reg = re.compile(r" '(.+)'")
            matches = reg.search(reg, str(e))
            marshaller.error.add(matches.groups()[0], 'Is required but not valid')
            return marshaller.errors.emit(), 422
