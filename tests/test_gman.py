import uuid

import pytest

from piedpiper_gman.gman import GMan

from piedpiper_gman.orm.models import (Task, TaskEvent)
#                                        TaskSchema, TaskEventSchema)

# API entrypoint tests ####
gman_task_create = {
    'run_id': 'create_1',
    'project': 'gman_test_data',
    'caller': 'test_case_create_1',
    'status': 'started',
    'message': 'a normal task creation body',
    'thread_id': 'pytest'
}

gman_task_event = {
    'task_id': '{}',
    'status': '{}',
    'message': 'Testing with status {}',
    'caller': 'test {}',
    'thread_id': '{}'
}

gman_task_create_post = [
    ({'run_id': '1',
      'project': 'pytest suite',
      'caller': 'test_case_1',
      'status': 'started',
      'message': 'test start with status == started'},
     200,
     [(lambda x: 'task_id' in x['task'], 'Missing "task_id"'),
      (lambda x: uuid.UUID(x['task']['task_id']), 'Invalid "task_id" UUID')]),
    ({'run_id': '2',
      'project': 'pytest suite',
      'caller': 'test_case_2',
      'message': 'test creation of a normal task no status'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned on 422'),
      (lambda x: 'status' in x['errors'], 'Did not error on status')]),
    ({'run_id': '4',
      'project': 'pytest suite',
      'caller': 'test_case_4',
      'status': 'info',
      'message': 'try to create a function with "info" status'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned'),
      (lambda x: 'status' in x['errors'],
       'Task allowed status other then started for a creation event')]),
    ({'run_id': '5',
      'task_id': 'ba279fdc-e11d-4bc8-828c-a44e35b55175',
      'project': 'pytest suite',
      'caller': 'test_case_5',
      'message': 'try to create task with a task_id'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned'),
      (lambda x: 'may not be specified on a post/create' in str(x['errors']),
       'Task creation allowed a defined task_id')]),
    ({'run_id': '6',
      'task_id': 'ba279fdc-e11d-4bc8-828c-a44e35b55175',
      'status': 'started',
      'project': 'pytest suite',
      'caller': 'test_case_6',
      'thread_id': 'should_not_be_allowed',
      'message': 'try to create task with a thread_id'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned'),
      (lambda x: 'may not be specified on a post/create' in str(x['errors']),
       'Task creation allowed a defined thread_id')]),
    ({'run_id': '7',
      'project': '9435b705-fbca-49a9-a4ab-400cc932bdd1',
      'caller': 'test_case_7',
      'status': 'started',
      'message': 'Test project is a UUID'},
     200,
     [(lambda x: uuid.UUID(x['task']['project']), 'Invalid "project" UUID')]),
    ({'run_id': '8',
      'project': 'pytest suite',
      'caller': 'test_case_8',
      'status': 'started',
      'timestamp': '2019-05-15T15:52:05.719859+00:00',
      'message': 'test defining valid timestamp'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned')]),
    ({'run_id': '9',
      'project': 'pytest suite',
      'caller': 'test_case_9',
      'status': 'started',
      'timestamp': '2019-dfdfd05-15T15:52:05.719859+00:00',
      'message': 'test defining invalid timestamp'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned')]),
    ({'project': 'pytest suite',
      'caller': 'test_case_10',
      'status': 'started',
      'message': 'testing missing run_id'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned')])
    ]


gman_put_statuses = [
    ('started', 422),
    ('completed', 200),
    ('failed', 200),
    ('delegated', 200),
    ('received', 200),
    ('info', 200)
]


@pytest.fixture
def test_task(api, client):
    return client.post(api.url_for(GMan), json=gman_task_create)


@pytest.mark.parametrize('data,resp_code,tests', gman_task_create_post)
def test_post(data, resp_code, tests, api, client):
    resp = client.post(api.url_for(GMan), json=data)

    assert resp.status_code == resp_code, f'Invalid response code {resp_code}'

    if tests:
        for test in tests:
            assert test[0](resp.json), test[1]


def test_post_w_task_id(api, client):
    data = {'run_id': '1_post_task',
            'project': '9435b705-fbca-49a9-a4ab-400cc932bdd1',
            'caller': 'test_post_w_task_id',
            'status': 'started',
            'message': 'Test project is a UUID'}
    resp = client.post(api.url_for(GMan, task_id='9435b705-fbca-49a9-a4ab-400cc932bdd1'),
                       json=data)

    assert resp.status_code == 422, f'Invalid response code {resp.status_code}'


@pytest.mark.parametrize('status,resp_code', gman_put_statuses)
def test_put_statuses(status, resp_code, api, client, test_task):
    task_id = test_task.json['task']['task_id']
    event = {
        'status': status,
        'message': f'Testing with status {status}',
        'caller': f'test put {status}',
        'thread_id': 'some_id'
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == resp_code, f'Invalid response code {resp_code}'


def test_put_bad_body(api, client, test_task):
    task_id = test_task.json['task']['task_id']
    event = {
        'status': 'asdfasdfsd',
        'message': f'Testing with status info bad body',
        'caller': f'test put info bad body',
        'thread_id': 'some_id'
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 422, f'Invalid response code {resp.status_code}'


def test_put_recieved_no_thread_id(api, client, test_task):
    task_id = test_task.json['task']['task_id']
    event = {
        'status': 'received',
        'message': f'Testing with status info bad body',
        'caller': f'test put info bad body',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 200, f'Invalid response code {resp.status_code}'


def test_put_bad_task_id(api, client):

    task_id = uuid.uuid4()
    event = {
        'status': 'info',
        'message': f'Testing with status info with /events',
        'caller': f'test put info with /events',
        'thread_id': 'some_id'
    }

    resp = client.put(api.url_for(GMan, task_id=task_id),
                      json=event)
    assert resp.status_code == 404, f'Expected 404 but got {resp.status_code}'


def test_put_w_events(api, client, test_task):

    task_id = test_task.json['task']['task_id']
    event = {
        'status': 'info',
        'message': f'Testing with status info with /events',
        'caller': f'test put info with /events',
        'thread_id': 'some_id'
    }

    resp = client.put(api.url_for(GMan, task_id=task_id, events='events'),
                      json=event)
    assert resp.status_code == 404, f'Expected 404 but got {resp.status_code}'


def test_get_bad_id(api, client):
    resp = client.get(api.url_for(GMan, task_id=uuid.uuid4()))

    assert resp.status_code == 404


def test_get_task(api, client, test_task):
    task_id = test_task.json['task']['task_id']

    resp = client.get(api.url_for(GMan, task_id=task_id))

    assert resp.status_code == 200
    assert resp.json['task_id'] == task_id, 'Bad task_id returned'


def test_get_task_events(api, client, test_task):
    task_id = test_task.json['task']['task_id']

    status = 'info'
    event = {
        'status': status,
        'message': f'Testing with status {status}',
        'caller': f'test put {status}',
        'thread_id': 'some_id'
    }

    client.put(api.url_for(GMan, task_id=task_id), json=event)

    resp = client.get(api.url_for(GMan, task_id=task_id, events='events'))

    assert resp.status_code == 200
    assert len(resp.json) == 2, 'Event count is off!'

    for event in resp.json:
        event['task']['task_id'] == task_id, 'Bad task_id returned'


def test_get_task_events_no_events(api, client, test_task):
    task_id = test_task.json['task']['task_id']

    task = Task.get(Task.task_id == task_id)

    TaskEvent.delete() \
             .where(TaskEvent.task == task) \
             .execute()

    events = TaskEvent.select() \
                      .join(Task) \
                      .where(Task.task_id == task_id)

    assert len([x for x in events]) == 0, 'events where not cleared out'

    resp = client.get(api.url_for(GMan, task_id=task_id, events='events'))

    assert resp.status_code == 404

# Functional tests ###
