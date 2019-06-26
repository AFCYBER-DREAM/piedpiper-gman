from flask_restful import Resource

from piperci_gman.orm.models import (Artifact, Task, TaskEvent, ZeroResults)


class PiperCiResource(Resource):

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

    def task_states(self, events):
        '''Parses task events to identify which state the task is in.'''

        running = ('started', 'received',)
        completed = ('completed',)
        failed = ('failed',)
        pending = ('delegated',)

        states = {'running': [],
                  'completed': [],
                  'failed': [],
                  'pending': [],
                  'received': []}

        pending_tasks = []

        for event in events:
            if event.status in running:
                if event.task not in states['running']:
                    states['running'].append(event.task)
                if event.status == 'received':
                    states['received'].append(event.task)

                    # Remove a matching parent task from pending
                    for pending in pending_tasks:
                        if pending.task_id == event.task.parent_id:
                            pending_tasks.remove(pending)
                            break

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

            elif event.status in pending:
                if event not in pending_tasks:
                    pending_tasks.append(event.task)

        states['pending'] = pending_tasks

        return states

    def task(self, task_id):
        return Task.get(Task.task_id == task_id)

    def task_events(self, task_id):
        events = [x for x in
                  TaskEvent.select()
                           .join(Task)
                           .where(Task.task_id == task_id)
                           .order_by(TaskEvent.timestamp)]
        if len(events):
            return events
        else:
            raise ZeroResults(f'No results returned for task_id: {task_id}')

    def task_thread(self, thread_id):
        return {event.task for event in self.task_event_thread(thread_id)}

    def task_event_thread(self, thread_id):
        events = [x for x in
                  TaskEvent.select()
                           .join(Task)
                           .where(Task.thread_id == thread_id)
                           .order_by(TaskEvent.timestamp)]
        if len(events):
            return events
        else:
            raise ZeroResults(f'No results returned for thread_id: {thread_id}')

    def tasks_run_id(self, run_id):
        tasks = [x for x in Task().select().where(Task.run_id == run_id)]
        if len(tasks):
            return tasks
        else:
            raise ZeroResults(f'No results returned for run_id: {run_id}')

    def task_events_run_id(self, run_id):
        events = [x for x in TaskEvent().select()
                                        .join(Task)
                                        .where(Task.run_id == run_id)
                                        .order_by(TaskEvent.timestamp)]
        if len(events):
            return events
        else:
            raise ZeroResults(f'No results returned for run_id: {run_id}')

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

    def task_completed_event(self, task_id):
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
