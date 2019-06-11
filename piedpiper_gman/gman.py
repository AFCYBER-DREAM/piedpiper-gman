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
        assert isinstance(errors, dict)
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

    def enforce(self, context):  # noqa: C901

        if context == 'create_task':

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

            disallowed = ('task_id', 'timestamp')

            if self.raw_data.get('status', '') not in ('started', 'received'):
                self.errors.add('status',
                                'Task creation must be \'started\' or \'received\'')
            else:
                if (self.raw_data.get('status') == 'received'
                        and not len(self.raw_data.get('thread_id', ''))):
                    self.errors.add('thread_id',
                                    'Thread_id is required for status received')

                if (self.raw_data.get('status', '') == 'started'
                        and not len(self.raw_data.get('thread_id', ''))):
                    self._task.data.thread_id = self._task.data.task_id

        elif context == 'add_event':
            disallowed = ('caller', 'thread_id', 'timestamp', 'project', 'run_id')

            self._event = TaskEventSchema().load(self.raw_data, partial=('timestamp',))

            try:
                self._event.data.timestamp = datetime.datetime.now()
            except AttributeError:
                self._event.data['timestamp'] = datetime.datetime.now()

            if self._event.errors:
                self.errors.extend(self._event.errors)

            if self.raw_data.get('status', '') in ('started', 'received'):
                self.errors.add('status',
                                'Updates may not be value \'started\' or \'received\'')

        for key in disallowed:
            if key in self.raw_data:
                self.errors.add(key, f'May not be specified for {context}')

        if len(self.errors.errors):
            raise MarshalError(self.errors)

    @property
    def task(self):
        return self._task

    @property
    def event(self):
        return self._event


class GMan(Resource):

    @property
    def NotFound(self):
        return {'message': 'Not Found'}, 404

    def get_task_states(self, events):
        '''Parses task events to identify which state the task is in.'''

        running = ('started', 'received')
        completed = ('completed',)
        failed = ('failed',)

        states = {'running': [],
                  'completed': [],
                  'failed': []}

        for event in events:
            if event.status in running:
                if event.task not in states['running']:
                    states['running'].append(event.task)
            elif event.status in completed:
                if event.task not in states['completed']:
                    states['completed'].append(event.task)
                if event.task in states['running']:
                    states['running'].remove(event.task)
            elif event.status in failed:
                if event.task not in states['failed']:
                    states['failed'].append(event.task)
                if event.task in states['running']:
                    states['running'].remove(event.task)

        return states

    def get_event_thread(self, thread_id):
        return [x for x in
                TaskEvent.select()
                         .join(Task)
                         .where(Task.thread_id == thread_id)
                         .order_by(TaskEvent.timestamp)]

    def get_task_events(self, task_id):
        return [x for x in
                TaskEvent.select()
                         .join(Task)
                         .where(Task.task_id == task_id)
                         .order_by(TaskEvent.timestamp)]

    def head(self, thread_id=None, events=None, task_id=None):

        if not (thread_id or task_id):
            return None, 404

        if thread_id:
            task_events = self.get_event_thread(thread_id)
        else:
            task_events = self.get_task_events(task_id)

        if len(task_events):

            if task_id:
                if events:
                    return None, 200, {'x-gman-events': len(task_events)}
                else:
                    # 1 task, should have a single state so find it
                    state = [k for k, v in self.get_task_states(task_events).items()
                             if len(v)][0]
                    return None, 200, {'x-gman-task-state': state}

            states = self.get_task_states(task_events)
            headers = {'x-gman-tasks-running': len(states['running']),
                       'x-gman-tasks-completed': len(states['completed']),
                       'x-gman-tasks-failed': len(states['failed'])}
            return None, 200, headers
        else:

            if task_id:
                if events:
                    return None, 404, {'x-gman-events': 0}
                else:
                    return None, 404, {'x-gman-task-state': 'not found'}

            headers = {'x-gman-tasks-running': 0,
                       'x-gman-tasks-completed': 0,
                       'x-gman-tasks-failed': 0}
            return None, 404, headers

    def get(self,  task_id=None, events=None, thread_id=None):

        if thread_id:
            event_thread = self.get_event_thread(thread_id)
            if not len(event_thread):
                return self.NotFound

            if events:
                return TaskEventSchema(many=True, exclude=['id']).dump(event_thread)
            else:
                tasks = {event.task for event in event_thread}
                return TaskSchema(many=True).dump(tasks)
        else:
            try:
                task = Task.get(Task.task_id == task_id)
            except DoesNotExist:
                return self.NotFound

            if events:
                events = self.get_task_events(task_id)

                if len(events):
                    return TaskEventSchema(many=True, exclude=['id']).dump(events)
                else:
                    return self.NotFound

            else:
                return TaskSchema().dump(task)

    def put(self, task_id, events=None, json=None):

        if events:
            return self.NotFound

        if json:
            raw = json
        else:
            raw = request.get_json(force=True)

        marshaller = GManMarshaller(raw)

        try:
            marshaller.enforce('add_event')
            task = Task.get(Task.task_id == task_id)
            try:
                # test for completed event
                events = [x for x in
                          (TaskEvent.select()
                                    .join(Task)
                                    .where(
                                        (Task.task_id == task_id)
                                        & (TaskEvent.status.in_(['failed', 'completed']))
                                    ))]

                marshaller.errors.add('status',
                                      f'A closing event for {events[0].task_id} of '
                                      f'{events[0].status} already exists.')

                return marshaller.errors.emit(), 422
            except IndexError:
                pass

            event = TaskEvent.create(task=task,
                                     message=marshaller.event.data.message,
                                     status=marshaller.event.data.status,
                                     timestamp=marshaller.event.data.timestamp)

            return TaskEventSchema(exclude=['id']).dump(event)

        except MarshalError as e:
            return e.errors.emit(), 422
        except DoesNotExist:
            return self.NotFound

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
            if marshaller.task.data.thread_id != marshaller.task.data.task_id:
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
                                  'Thread_id must be an existing task_id')
            return marshaller.errors.emit(), 422
        except AttributeError as e:
            reg = re.compile(r" '(.+)'")
            matches = reg.search(str(e))
            marshaller.errors.add(matches.groups()[0], 'Is required but not valid')
            return marshaller.errors.emit(), 422
