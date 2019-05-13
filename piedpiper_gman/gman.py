import datetime
import uuid

from flask import request
from flask_restful import Resource
from peewee import DoesNotExist
from piedpiper_gman.orm.models import (Task,
                                       TaskEvent,
                                       TaskSchema,
                                       TaskEventSchema)


class GMan(Resource):

    def get(self, task_id, events=None):
        try:
            task = Task.get(Task.task_id == task_id)
        except DoesNotExist:
            return {'message': 'Not Found'}, 404

        if events:
            try:
                events = TaskEvent.select() \
                            .join(Task) \
                            .where(Task.task_id == task_id) \
                            .order_by(TaskEvent.timestamp)

                return TaskEventSchema(many=True, exclude=['id']).dump(events)
            except DoesNotExist:
                return {'message': 'Not Found'}, 404
        else:
            return TaskSchema().dump(task)

    def put(self, task_id, events=None):

        if events:
            return {'message': 'Not Found'}, 404

        raw = request.get_json(force=True)

        now = datetime.datetime.now()
        event_marsh = TaskEventSchema().load(raw, partial=('timestamp',))

        try:
            task = Task.get(Task.task_id == task_id)
        except DoesNotExist:
            return {'message': 'Not Found'}, 404

        if event_marsh.errors:
            return {'errors': event_marsh.errors}, 422

        event_data = event_marsh.data

        if event_data.status == 'started':
            return {'errors': {'status':
                               ['updates may not be value \'started\'']}}, 422

        if not event_data.thread_id and event_data.status == 'recieved':
            event_data.thread_id = uuid.uuid4()

        event = TaskEvent.create(task=task,
                                 message=event_data.message,
                                 status=event_data.status,
                                 timestamp=now,
                                 thread_id=event_data.thread_id)

        return TaskEventSchema(exclude=['id']).dump(event)

    def post(self, *args, **kwargs):
        if len(args) or len(kwargs):
            return {'message': 'Not Found'}, 404

        raw = request.get_json(force=True)
        errors = {'errors': {}}

        for disallowed in ('task_id', 'timestamp', 'thread_id'):
            if disallowed in raw:
                errors.setdefault(disallowed, []).append(
                    'may not be specified on a post/create')

        if len(errors['errors']):
            return errors, 422

        # strftime('%Y-%m-%d %H:%M')
        # raw['timestamp'] == iso8601 "2019-05-10T13:59:37.815929+00:00"
        now = datetime.datetime.now()
        task_marsh = TaskSchema().load(raw)
        event_marsh = TaskEventSchema().load(raw, partial=('timestamp',))

        if task_marsh.errors:
            return {'errors': task_marsh.errors}, 422
        else:
            task_data = task_marsh.data

        if event_marsh.errors:
            return {'errors': event_marsh.errors}, 422
        else:
            event_data = event_marsh.data

        if event_data.status != 'started':
            return {'errors': {'status':
                               ['creation must be value \'started\'']}}, 422

        task = Task.create(task_id=task_data.task_id,
                           run_id=task_data.run_id,
                           caller=task_data.caller,
                           project=task_data.project)

        event = TaskEvent.create(task=task,
                                 message=event_data.message,
                                 status=event_data.status,
                                 timestamp=now,
                                 thread_id='')

        return TaskEventSchema(exclude=['id']).dump(event)
