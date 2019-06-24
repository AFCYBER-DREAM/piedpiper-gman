from flask_restful import Resource

from piedpiper_gman.orm.models import (Artifact, Task, TaskEvent, ZeroResults)


class PiedPiperResource(Resource):

    def BadRequest(self, message=None):
        message = f': {message}' if message else ''
        return ({'message':
                 f'Bad Request - Could not execute based on sent params{message}'},
                400)

    def NotFound(self, message=None):
        message = f': {message}' if message else ''
        return ({'message': 'Not Found{message}'}, 404)

    def InternalError(self, message=None):
        message = f': {message}' if message else ''
        return ({'message': f'Internal Server Error{message}'}, 500)

    def get_task_states(self, events):
        '''Parses task events to identify which state the task is in.'''

        running = ('started', 'received',)
        completed = ('completed',)
        failed = ('failed',)

        states = {'running': [],
                  'completed': [],
                  'failed': [],
                  'pending': []}

        for event in events:
            if event.status in running:
                if event.task not in states['running']:
                    states['running'].append(event.task)
                if event.status == 'received':
                    states['pending'].pop()
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
            elif event.status == 'delegated':
                if event.task not in states['pending']:
                    states['pending'].append(event.task)

        return states

    def artifacts_by_task_id(self, task_id):
        arts = [x for x in Artifact.select()
                                   .join(Task)
                                   .join(TaskEvent)
                                   .distinct()
                                   .where(
                                       (Task.task_id == task_id)
                                       & (Artifact.task_id == Task.task_id)
                                       & (TaskEvent.event_id == Artifact.event_id))
                                   .order_by(TaskEvent.timestamp)]

        if len(arts):
            return arts
        else:
            raise ZeroResults(f'No results returned for task_id: {task_id}')

    def artifacts_by_sri(self, sri, validate=False):
        arts = [x for x in Artifact.select()
                                   .join(TaskEvent)
                                   .distinct()
                                   .where((Artifact.sri == sri)
                                          & (TaskEvent.event_id == Artifact.event_id))
                                   .order_by(TaskEvent.timestamp)]
        if len(arts):
            return arts
        else:
            raise ZeroResults(f'No results returned for sri: {sri}')

    def get_event_thread(self, thread_id):
        events = [x for x in
                  TaskEvent.select()
                           .join(Task)
                           .where(Task.thread_id == thread_id)
                           .order_by(TaskEvent.timestamp)]
        if len(events):
            return events
        else:
            raise ZeroResults(f'No results returned for thread_id: {thread_id}')

    def get_task_events(self, task_id):
        events = [x for x in
                  TaskEvent.select()
                           .join(Task)
                           .where(Task.task_id == task_id)
                           .order_by(TaskEvent.timestamp)]
        if len(events):
            return events
        else:
            raise ZeroResults(f'No results returned for task_id: {task_id}')

    def get_task_completed_event(self, task_id):
        events = [x for x in
                  (TaskEvent.select()
                            .join(Task)
                            .where(
                                (Task.task_id == task_id)
                                & (TaskEvent.status.in_(['failed', 'completed']))
                            ))]

        if len(events):
            return events[0]
        else:
            raise ZeroResults(f'No results returned for task_id: {task_id}')
