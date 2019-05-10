import datetime

from flask import request
from flask_restful import Resource
from piedpiper_gman.orm.models import (Task, TaskEvent, TaskEventSchema)


class GMan(Resource):

    def get(self, task_id=None):

        if task_id:
            TaskEvent.get(Task.task_id == task_id)
            return ({'hello': 'world'}, 200)
        return {}, 200

    def post(self):
        data = request.get_json(force=True)

        # strftime('%Y-%m-%d %H:%M')
        now = datetime.datetime.now()
        import pdb; pdb.set_trace()
        y = TaskEventSchema().load(data)

        task = Task.create(run_id=data['run_id'],
                           caller=data['caller'],
                           project=data['project'])

        task_event = TaskEvent.create(task=task,
                                      message=data['message'],
                                      status=data['status'],
                                      timestamp=now)

        x = TaskEventSchema().dump(task_event)
        return x

    def put(self, task_id):
        return None
