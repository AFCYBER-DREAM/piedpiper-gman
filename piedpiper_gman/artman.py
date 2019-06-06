
from flask import request
from peewee import DoesNotExist
from piedpiper_gman.orm.models import (Task,
                                       TaskEvent,
                                       Artifact,
                                       TaskSchema,
                                       ArtifactSchema,
                                       QueryFailed,
                                       ZeroResults)

from piedpiper_gman.gman import GMan
from piedpiper_gman.marshaller import Marshaller, MarshalError
from piedpiper_gman.resource import PiedPiperResource

from werkzeug.exceptions import BadRequest


class ArtManMarshaller(Marshaller):

    def __init__(self, raw):
        super(ArtManMarshaller, self).__init__(raw)

        self._artifact = None
        self._task = None

    def enforce(self, context=None):

        disallowed = ('artifact_id', 'timestamp', 'status', 'event_id')

        required = ('task_id',)

        for key in disallowed:
            if key in self.raw_data:
                self.errors.add(key, f'May not be specified for {context}',
                                data=self.raw_data)

        for key in required:
            if key not in self.raw_data:
                self.errors.add(key, f'Must be specified for {context}',
                                data=self.raw_data)

        self.raw_data['status'] = 'unknown'

        self._artifact = ArtifactSchema().load(self.raw_data,
                                               partial=('event_id',))

        self._task = TaskSchema().load(self.raw_data,
                                       partial=('thread_id', 'caller',
                                                'project', 'run_id'))

        if self._artifact.errors:
            self.errors.extend(self._artifact.errors,
                               data=self._artifact)

        if self._task.errors:
            self.errors.extend(self._task.errors,
                               data=self._task)

        if len(self.errors.errors):
            raise MarshalError(self.errors)

    @property
    def artifact(self):
        return self._artifact

    @property
    def task(self):
        return self._task


class ArtMan(PiedPiperResource):

    def head(self, artifact=None, task_id=None, sri=None):
        try:
            if artifact:
                art = Artifact.get_by_id(str(artifact))
                return None, 200, {'x-gman-artifact-status': art.status}
            elif task_id:
                arts = self.artifacts_by_task_id(task_id)
                return None, 200, {'x-gman-artifacts': len(arts)}
            elif sri:
                arts = self.artifacts_by_sri(sri)
                return None, 200, {'x-gman-artifacts': len(arts)}
            else:
                return None, 400
        except (ZeroResults, DoesNotExist):
            return None, 404

    def get(self, artifact=None, task_id=None, sri=None):
        try:
            if artifact:
                return ArtifactSchema().dump(Artifact.get_by_id(str(artifact)))
            elif task_id:
                arts = self.artifacts_by_task_id(task_id)
                return ArtifactSchema(many=True, exclude=['id']).dump(arts)
            elif sri:
                arts = self.artifacts_by_sri(sri, validate=True)
                return ArtifactSchema(many=True).dump(arts)
            else:
                return self.BadRequest()
        except (ZeroResults, DoesNotExist):
            return self.NotFound()

    def post(self, *args, **kwargs):

        try:
            if len(args) or len(kwargs):
                raise BadRequest('Invalid args specified for POST')

            raw = request.get_json(force=True)

            marshaller = ArtManMarshaller(raw)
            marshaller.enforce('create_artifact')
            task = Task.get(Task.task_id == marshaller.task.data.task_id)
            try:
                # exact duplicate artifact post detection
                artifact = Artifact.get(
                    (Artifact.sri == marshaller.artifact.data.sri)
                    & (Artifact.task_id == marshaller.task.data.task_id))
                marshaller.errors.add('sri', 'Artifact Exists')
                marshaller.errors.add('event_id', 'Artifact Exists')
                return marshaller.errors.emit(), 409
            except DoesNotExist:
                # create an event for this artifact and store
                event = GMan.put(self, task.task_id,
                                 json={'status': 'info',
                                       'message': 'Adding artifact'})

                event = TaskEvent.get(TaskEvent.event_id == event.data['event_id'])

                art_status = marshaller.artifact.data.status

                artifact = Artifact.create(task=task,
                                           event_id=event,
                                           type=marshaller.artifact.data.type,
                                           status=art_status,
                                           sri=marshaller.artifact.data.sri,
                                           uri=marshaller.artifact.data.uri)

                if not artifact:
                    raise QueryFailed(
                        f'Failed to create artifact for task {task.task_id}')

            return ArtifactSchema().dump(artifact)
        except MarshalError as e:
            return e.errors.emit(), 422
        except DoesNotExist:
            marshaller.errors.add('task_id', 'does not exist')
            return marshaller.errors.emit(), 404
        except BadRequest as e:
            return self.BadRequest(str(e))
        except (QueryFailed, Exception) as e:
            return self.InternalError(str(e))
