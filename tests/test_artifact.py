import datetime

import pytest

from piperci_gman.artman import ArtMan
from piperci_gman.orm.models import Artifact, Task, TaskEvent, db

_artifacts = [
    {'uri': 'https://someminio.example.com/art1',
     'sri': 'sha256-sCDaaxdshXhK4sA/v4dMHiMWhtGyQwA1fP8PgrN0O5g=',
     'sri-urlsafe':
         'c2hhMjU2LXNDRGFheGRzaFhoSzRzQS92NGRNSGlNV2h0R3lRd0ExZlA4UGdyTjBPNWc9',
     'type': 'artifact',
     'caller': 'pytest'},
    {'uri': 'https://someminio.example.com/art2',
     'sri': 'sha256-jrT+J2yEC8wfUr6N/YxxbR/ux5y2GriIqXsySl5uVK8=',
     'sri-urlsafe':
         'c2hhMjU2LWpyVCtKMnlFQzh3ZlVyNk4vWXh4YlIvdXg1eTJHcmlJcVhzeVNsNXVWSzg9',
     'type': 'source',
     'caller': 'pytest'},
    {'uri': 'https://someminio.example.com/art1',
     'sri': 'sha256-sCDaaxdshXhK4sA/v4dMHiMWhtGyQwA1fP8PgrN0O5g=',
     'sri-urlsafe':
         'c2hhMjU2LXNDRGFheGRzaFhoSzRzQS92NGRNSGlNV2h0R3lRd0ExZlA4UGdyTjBPNWc9',
     'type': 'artifact',
     'caller': 'pytest',
     'task_id': 'New'},
    ]


def formateach(data, values):
    i = 0
    for k, v in data.items():
        try:
            data[k] = v.format(values[i])
            i += 1
        except IndexError:
            raise ValueError('Ran out of values to fill dict')


@pytest.fixture
def artifact(api, client, testtask):
    task = testtask()
    data = {'task_id': task.json['task']['task_id']}
    data.update(_artifacts[0])
    resp = client.post(api.url_for(ArtMan), json=data)
    return resp.json, data


@pytest.fixture
def artifacts(api, client, testtask):
    task = testtask()
    arts = []

    for artifact in _artifacts:
        if 'task_id' in artifact and artifact['task_id'] == 'New':
            _task = testtask()
        else:
            _task = task

        data = {}
        data.update(artifact)
        data['task_id'] = _task.json['task']['task_id']

        resp = client.post(api.url_for(ArtMan), json=data)
        # assert resp.status_code == 200
        if resp.status_code != 200:
            pytest.fail(str(resp.json) + str(data))
        arts.append((resp,
                     data))

    return arts


def test_get_artifact(api, client, artifacts):

    for artifact in artifacts:
        art_id = artifact[0].json['artifact_id']
        resp = client.get(f'/artifact/{art_id}')
        assert resp.status_code == 200


def test_get_artifact_bad_request(api, client):
    resp = client.get('/artifact')
    assert resp.status_code == 400


def test_get_bad_artifact(api, client, artifacts):
    resp = client.get(f'/artifact/31a122e8-9ba8-4f60-a9fb-490c66fd4b0a')
    assert resp.status_code == 404


def test_get_artifacts_by_task_id(api, client, artifact):
    task_id = artifact[0]['task']['task_id']

    resp = client.get(api.url_for(ArtMan, task_id=task_id))
    assert len(resp.json) == 1
    assert resp.json[0]['task']['task_id'] == task_id


def test_get_artifacts_by_bad_task_id(api, client, artifact):
    task_id = '31a122e8-9ba8-4f60-a9fb-490c66fd4b0a'

    resp = client.get(api.url_for(ArtMan, task_id=task_id))
    assert resp.status_code == 404


def test_get_artifact_by_bad_sri(api, client, artifact):
    bad_sri = 'c2hhMjU2LXZGYXRjZXlXYUU5QWtzM045b3VSVXRiYTFtd3JJSGRFVkx0aTg4YXRJdmM9'
    resp = client.get(f'/artifact/sri/{bad_sri}')
    assert resp.status_code == 404


def test_get_artifacts_by_sri(api, client, artifacts):
    resp = client.get(f'/artifact/sri/{artifacts[0][1]["sri-urlsafe"]}')
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_head_artifact_bad_request(api, client):
    resp = client.head('/artifact')
    assert resp.status_code == 400


def test_head_artifact(api, client, artifacts):

    for artifact in artifacts:
        art_id = artifact[0].json['artifact_id']
        resp = client.head(f'/artifact/{art_id}')
        assert resp.status_code == 200
        assert resp.headers['x-gman-artifact-status'] == 'unknown'


def test_head_bad_artifact(api, client, artifacts):

    resp = client.head(f'/artifact/31a122e8-9ba8-4f60-a9fb-490c66fd4b0a')
    assert resp.status_code == 404


def test_head_artifacts_by_sri(api, client, artifacts):
    resp = client.head(f'/artifact/sri/{artifacts[0][1]["sri-urlsafe"]}')
    assert resp.status_code == 200
    assert int(resp.headers['x-gman-artifacts']) == 2


def test_head_artifacts_for_task_id(api, client, artifact):
    task_id = artifact[0]['task']['task_id']

    resp = client.head(api.url_for(ArtMan, task_id=task_id))
    assert int(resp.headers['x-gman-artifacts']) == 1


def test_put_artifact(api, client):

    resp = client.put(api.url_for(ArtMan))

    assert resp.status_code == 405


def test_post_artifact_no_task(api, client):
    art = {'task_id': '7d394a53-6f45-4847-bfd1-105eef07dd08'}

    art.update(_artifacts[0])
    resp = client.post(api.url_for(ArtMan), json=art)

    assert resp.status_code == 404, 'Code failed to check that the task exists'
    assert 'errors' in resp.json, 'Missing expected errors response'
    assert 'task_id' in resp.json['errors'], (
        'Did not throw the correct error for this test')


def test_post_bad_artifact_url(api, client):

    resp = client.post('/artifact/31a122e8-9ba8-4f60-a9fb-490c66fd4b0a')
    assert resp.status_code == 400


def test_post_same_artifact_twice(api, client, artifact):

    art = {'task_id': artifact[0]['task']['task_id']}
    art.update(_artifacts[0])

    resp = client.post(api.url_for(ArtMan), json=art)

    assert resp.status_code == 409


@pytest.mark.parametrize('dissallowed', ('artifact_id', 'timestamp',
                                         'status', 'event_id'))
def test_post_dissallowed_field(api, client, dissallowed):

    art = _artifacts[0].copy()
    art[dissallowed] = 'Some value'
    resp = client.post(api.url_for(ArtMan), json=art)
    assert resp.status_code == 422


def test_post_field_value_errors(api, client):

    art = _artifacts[0].copy()
    art['type'] = 'asdfasdfs'
    art['task_id'] = 1234
    resp = client.post(api.url_for(ArtMan), json=art)
    assert resp.status_code == 422


def test_raw_artifact_bad_hash(testtask):
    task_resp = testtask()
    task = Task().get(Task.task_id == task_resp.json['task']['task_id'])

    event = TaskEvent.create(task=task,
                             message='testing creating an artifact',
                             status='info',
                             timestamp=datetime.datetime.now())
    with pytest.raises(ValueError):
        Artifact().create(
            task=task,
            event_id=event,
            type='log',
            status='unknown',
            sri='some non sri value',
            uri='https://www.example.com'
        )


def test_failed_artifact_create_no_table(api, client, monkeypatch, testtask):
    task = testtask()

    db.drop_tables([Artifact])

    art = {'task_id': task.json['task']['task_id']}
    art.update(_artifacts[0])

    resp = client.post(api.url_for(ArtMan), json=art)
    assert resp.status_code == 500


def test_failed_artifact_create_IDK(api, client, monkeypatch, testtask):
    task = testtask()

    def myfunc(*args, **kwargs):
        kwargs['uri'] = {'not a valid thing'}
        return None

    monkeypatch.setattr('piperci_gman.orm.models.Artifact.create', myfunc)

    art = {'task_id': task.json['task']['task_id']}
    art.update(_artifacts[0])

    resp = client.post(api.url_for(ArtMan), json=art)
    assert resp.status_code == 500
