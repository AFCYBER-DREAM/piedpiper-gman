import datetime
import re

from flask import request
from peewee import DoesNotExist

from piperci_gman.orm.models import (Task,
                                     TaskEvent,
                                     TaskSchema,
                                     TaskEventSchema,
                                     QueryFailed,
                                     ZeroResults)

from piperci_gman.marshaller import Marshaller, MarshalError
from piperci_gman.resource import PiperCiResource

from werkzeug.exceptions import BadRequest


class GManMarshaller(Marshaller):

    def __init__(self, raw):
        super(GManMarshaller, self).__init__(raw)

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


class GMan(PiperCiResource):

    def head(self, thread_id=None, events=None, task_id=None):

        try:
            if thread_id:
                task_events = self.get_event_thread(thread_id)

                states = self.get_task_states(task_events)
                headers = {'x-gman-tasks-running': len(states['running']),
                           'x-gman-tasks-completed': len(states['completed']),
                           'x-gman-tasks-pending': len(states['pending']),
                           'x-gman-tasks-failed': len(states['failed'])}
                return None, 200, headers
            elif task_id:
                task_events = self.get_task_events(task_id)

                if events:
                    return None, 200, {'x-gman-events': len(task_events)}
                else:
                    state = [k for k, v in self.get_task_states(task_events).items()
                             if len(v)][0]
                    return None, 200, {'x-gman-task-state': state}
            else:
                raise BadRequest('No action specified')
        except ZeroResults:
            if task_id:
                if events:
                    return None, 404, {'x-gman-events': 0}
                else:
                    return None, 404, {'x-gman-task-state': 'not found'}
            else:
                headers = {'x-gman-tasks-running': 0,
                           'x-gman-tasks-completed': 0,
                           'x-gman-tasks-failed': 0}
                return None, 404, headers
        except BadRequest:
            return None, 400

    def get_thread(self, thread_id, events=None):
        event_thread = self.get_event_thread(thread_id)
        if events:
            return TaskEventSchema(many=True, exclude=['id']).dump(event_thread)
        else:
            tasks = {event.task for event in event_thread}
            return TaskSchema(many=True).dump(tasks)

    def get_task(self, task_id=None, run_id=None, events=None):
        if task_id:
            task = Task.get(Task.task_id == task_id)
        elif run_id:
            task = Task.get(Task.run_id == run_id)
            task_id = task.task_id
        else:
            return

        if events:
            events = self.get_task_events(task_id)
            return TaskEventSchema(many=True, exclude=['id']).dump(events)
        else:
            return TaskSchema().dump(task)

    def get(self, task_id=None, run_id=None, events=None, thread_id=None):
        try:
            if thread_id:
                return self.get_thread(thread_id, events)
            elif task_id:
                return self.get_task(task_id=task_id, events=events)
            elif run_id:
                return self.get_task(run_id=run_id, events=events)
            else:
                raise BadRequest('No action specified')
        except (ZeroResults, DoesNotExist):
            return self.NotFound()
        except BadRequest as e:
            return self.BadRequest(str(e))

    def put(self, task_id, events=None, json=None):

        try:
            if events:
                raise BadRequest('Events may not be specified on a PUT')

            if json:
                raw = json
            else:
                raw = request.get_json(force=True)

            marshaller = GManMarshaller(raw)
            marshaller.enforce('add_event')
            task = Task.get(Task.task_id == task_id)
            try:
                completed = self.get_task_completed_event(task_id)
                marshaller.errors.add('status',
                                      f'A closing event for {completed.task_id} of '
                                      f'{completed.status} already exists.')

                return marshaller.errors.emit(), 422
            except ZeroResults:
                pass

            event = TaskEvent.create(task=task,
                                     message=marshaller.event.data.message,
                                     status=marshaller.event.data.status,
                                     timestamp=marshaller.event.data.timestamp)
            if event:
                return TaskEventSchema().dump(event)
            else:
                raise QueryFailed(f'Event Creation Error for task_id {task_id}')

        except MarshalError as e:
            return e.errors.emit(), 422
        except DoesNotExist:
            return self.NotFound()
        except BadRequest as e:
            return self.BadRequest(str(e))
        except Exception as e:
            return self.InternalError(str(e))

    def post(self, *args, **kwargs):

        try:
            if 'task_id' in kwargs or 'events' in kwargs:
                raise BadRequest('Invalid args for this method')

            if 'json' in kwargs:
                raw = kwargs['json']
            else:
                raw = request.get_json(force=True)

            marshaller = GManMarshaller(raw)
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
        except BadRequest as e:
            return self.BadRequest(str(e))
        except Exception as e:
            return self.InternalError(str(e))
