import uuid

import pytest

from piedpiper_gman.gman import GMan
from piedpiper_gman.marshaller import Errors

from piedpiper_gman.orm.models import (Task, TaskEvent, db)

gman_task_event = {
    'task_id': '{}',
    'status': '{}',
    'message': 'Testing with status {}',
    'caller': 'test {}'
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
      'message': 'try to create task with a task_id',
      'status': 'started'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned'),
      (lambda x: 'May not be specified for create_task' in str(x['errors']),
       'Task creation allowed a defined task_id')]),
    ({'run_id': '6',
      'status': 'started',
      'project': 'pytest suite',
      'caller': 'test_case_6',
      'thread_id': 'ba279fdc-e11d-4bc8-828c-a44e35b55175',
      'message': 'thread_id must be an existing task_id'},
     422,
     [(lambda x: 'Thread_id must be an existing task_id' in x['errors']['thread_id'],
       'thread_id was allowed for not existing task')]),
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
     [(lambda x: 'errors' in x, 'No error message returned')]),
    ({'project': 'pytest suite',
      'caller': 'test_case_11',
      'status': 'started',
      'return_code': 'bad_value',
      'run_id': '5',
      'message': 'testing invalid return_code'},
     422,
     [(lambda x: 'errors' in x, 'No error message returned'),
      (lambda x: 'return_code' in x['errors'], 'Return code check missing')]),
    ({'project': 'pytest suite',
      'caller': 'test_case_12',
      'status': 'started',
      'return_code': 21,
      'run_id': '5',
      'message': 'testing invalid return_code'},
     200,
     [(lambda x: 'return_code' in x, 'return_code not in task')])
    ]


gman_put_statuses = [
    ('started', 422),
    ('completed', 200),
    ('failed', 200),
    ('delegated', 200),
    ('received', 422),
    ('info', 200)
]


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

    assert resp.status_code == 400, f'Invalid response code {resp.status_code}'


gman_post_delegated = [
        ({'run_id': '1',
          'project': 'pytest suite',
          'caller': 'test_post_delegated_1',
          'status': 'received',
          'message': 'test create with status == received no thread_id'},
         422,
         [(lambda x: 'Thread_id is required for status received'
                     in x['errors']['thread_id'],
                     'thread_id was not required for status received')]),
        ({'run_id': '2',
          'project': 'pytest suite',
          'caller': 'test_post_delegated_2',
          'status': 'received',
          'thread_id': '9435b705-fbca-49a9-a4ab-400cc932bdd1',
          'message': 'test create with status == received bad thread_id'},
         422,
         [(lambda x: 'Thread_id must be an existing task_id'
                     in x['errors']['thread_id'],
                     'thread_id was allowed to be created for a non-existing task')]),
        ({'run_id': '3',
          'project': 'pytest suite',
          'caller': 'test_post_delegated_3',
          'status': 'received',
          'thread_id': '{}',
          'message': 'test create with status == received good thread_id'},
         200,
         [(lambda x: 'errors' not in x, 'errors detected on expected good post')]),
        ]


@pytest.mark.parametrize('data,resp_code,tests', gman_post_delegated)
def test_post_delegated(data, resp_code, tests, api, client, testtask):
    thread_id = testtask().json['task']['task_id']

    if 'thread_id' in data and data['thread_id'] == '{}':
        data['thread_id'] = data['thread_id'].format(thread_id)
    resp = client.post(api.url_for(GMan), json=data)

    assert resp.status_code == resp_code, f'Invalid response code {resp_code}'

    if tests and len(tests):
        for test in tests:
            assert test[0](resp.json), test[1]


def test_post_no_body(api, client):

    resp = client.post(api.url_for(GMan))
    assert resp.status_code == 400


def test_put_not_body(api, client):

    resp = client.put(api.url_for(GMan))

    assert resp.status_code == 400


@pytest.mark.parametrize('status,resp_code', gman_put_statuses)
def test_put_statuses(status, resp_code, api, client, testtask):
    task_id = testtask().json['task']['task_id']
    event = {
        'status': status,
        'message': f'Testing with status {status}'
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == resp_code, f'Invalid response code {resp_code}'


def test_put_bad_body(api, client, testtask):
    task_id = testtask().json['task']['task_id']
    event = {
        'status': 'asdfasdfsd',
        'message': f'Testing with status info bad body',
        'caller': f'test put info bad body',
        'thread_id': 'some_id'
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 422, f'Invalid response code {resp.status_code}'


def test_put_bad_task_id(api, client):

    task_id = uuid.uuid4()
    event = {
        'status': 'info',
        'message': f'Testing with status info with /events',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id),
                      json=event)
    assert resp.status_code == 404, f'Expected 404 but got {resp.status_code}'


def test_put_w_events(api, client, testtask):

    task_id = testtask().json['task']['task_id']
    event = {
        'status': 'info',
        'message': f'Testing with status info with /events',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id, events='events'),
                      json=event)
    assert resp.status_code == 400, f'Expected 400 but got {resp.status_code}'


def test_get_bad_id(api, client):
    resp = client.get(api.url_for(GMan, task_id=uuid.uuid4()))

    assert resp.status_code == 404


def test_get_task(api, client, testtask):
    task_id = testtask().json['task']['task_id']

    resp = client.get(api.url_for(GMan, task_id=task_id))

    assert resp.status_code == 200
    assert resp.json['task_id'] == task_id, 'Bad task_id returned'


def test_get_task_no_task_id(api, client, testtask):

    resp = client.get(api.url_for(GMan))

    assert resp.status_code == 400


def test_head_task_no_task_id(api, client, testtask):

    resp = client.head(api.url_for(GMan))

    assert resp.status_code == 400


def test_get_task_events(api, client, testtask):
    task_id = testtask().json['task']['task_id']

    event = {
        'status': 'info',
        'message': f'Testing with status info',
    }

    client.put(api.url_for(GMan, task_id=task_id), json=event)

    resp = client.get(api.url_for(GMan, task_id=task_id, events='events'))

    assert resp.status_code == 200
    assert len(resp.json) == 2, 'Event count is off!'

    for event in resp.json:
        event['task']['task_id'] == task_id, 'Bad task_id returned'


@pytest.mark.parametrize('status', ['failed', 'completed'])
def test_put_info_failed_event(status, api, client, testtask):
    task_id = testtask().json['task']['task_id']

    event = {
        'status': f'{status}',
        'message': f'Testing with status {status}',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 200, 'first part closing event with {status} failed'

    event = {
            'status': 'info',
            'message': f'Testing with status info',
        }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)

    assert resp.status_code == 422, 'should fail to add an event to closed task'
    assert 'A closing event for' in str(resp.json['errors']['status'])


def test_get_task_events_no_events(api, client, testtask):
    task_id = testtask().json['task']['task_id']

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


def test_head_task_id(api, client, testtask):

    task_id = testtask().json['task']['task_id']

    event = {
        'status': f'info',
        'message': f'Testing with status info',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 200, 'first part closing event with {status} failed'

    resp = client.head(f'/task/{task_id}')
    assert resp.headers['x-gman-task-state'] == 'running'


def test_head_task_id_events(api, client, testtask):

    task_id = testtask().json['task']['task_id']

    event = {
        'status': f'info',
        'message': f'Testing with status info',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 200, 'first part closing event with {status} failed'

    resp = client.head(f'/task/{task_id}/events')
    assert 'x-gman-events' in resp.headers
    assert int(resp.headers['x-gman-events']) == 2


@pytest.fixture
def testthread(api, client, testtask):
    task = testtask()
    task_id = task.json['task']['task_id']

    event = {
        'status': f'info',
        'message': f'Testing with status info',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 200, 'first part closing event with {status} info'

    new_task = {
        'thread_id': task_id,
        'message': 'adding an open task',
        'status': 'received',
        'run_id': task.json['task']['run_id'],
        'caller': 'pytest_next_task',
        'project': 'pytest'
    }

    resp = testtask(json=new_task)
    assert resp.status_code == 200, 'failed to create delegated task'

    event = {
        'status': f'delegated',
        'message': f'Delegated new task {resp.json["task"]["task_id"]}',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 200, 'marking a delegated task'

    event = {
        'status': f'completed',
        'message': f'Testing with status completed',
    }

    resp = client.put(api.url_for(GMan, task_id=task_id), json=event)
    assert resp.status_code == 200, 'first part closing event with status completed'

    event = {
        'status': f'failed',
        'message': f'Testing with status failed',
    }

    task2_resp = client.post(api.url_for(GMan), json=new_task)
    assert resp.status_code == 200, 'failed to create delegated task2'

    resp = client.put(api.url_for(GMan, task_id=task2_resp.json['task']['task_id']),
                      json=event)
    assert resp.status_code == 200, 'first part closing event with status completed'

    return task_id


def test_head_thread_events(api, client, testthread):
    resp = client.head(f'/thread/{testthread}')
    assert 'x-gman-tasks-running' in resp.headers
    assert 'x-gman-tasks-completed' in resp.headers
    assert 'x-gman-tasks-failed' in resp.headers

    assert int(resp.headers['x-gman-tasks-completed']) == 1
    assert int(resp.headers['x-gman-tasks-running']) == 1
    assert int(resp.headers['x-gman-tasks-failed']) == 1


def test_get_thread(api, client, testthread):

    resp = client.get(f'/thread/{testthread}')

    assert resp.status_code == 200
    for task in resp.json:
        assert 'task_id' in task, 'not a valid task json response'


def test_get_thread_events(api, client, testthread):

    resp = client.get(f'/thread/{testthread}/events')

    assert resp.status_code == 200
    for event in resp.json:
        assert 'task' in event, 'not a valid task event, must have a task'
        assert isinstance(event['task'], dict), 'task must be a dict'


def test_get_thread_bad_id(api, client):
    resp = client.get('/thread/9435b705-fbca-49a9-a4ab-400cc932bdd1')
    assert resp.status_code == 404


def test_head_non_existing_thread(api, client):
    resp = client.head('/thread/9435b705-fbca-49a9-a4ab-400cc932bdd1')
    assert int(resp.headers['x-gman-tasks-completed']) == 0
    assert int(resp.headers['x-gman-tasks-running']) == 0
    assert int(resp.headers['x-gman-tasks-failed']) == 0


def test_head_non_existing_task_events(api, client):
    resp = client.head(f'/task/9435b705-fbca-49a9-a4ab-400cc932bdd1/events')
    assert int(resp.headers['x-gman-events']) == 0


def test_head_non_existing_task(api, client):
    resp = client.head(f'/task/9435b705-fbca-49a9-a4ab-400cc932bdd1')
    assert resp.headers['x-gman-task-state'] == 'not found'


def test_head_gman_task(api, client, testtask):
    testtask()
    resp = client.head('/task')
    resp.status_code == 404


def test_errors_extend_is_dict():

    errors = Errors()

    with pytest.raises(AssertionError):
        errors.extend('something')


def test_errors_extend():

    errors = Errors()

    errors.extend({'x': ['this is a test error']})
    errors.extend({'x': ['another test']})

    assert 'this is a test error' in errors.errors['x']
    assert 'another test' in errors.errors['x']


def test_failed_event_create_no_table(api, client, monkeypatch, testtask):
    task = testtask()

    db.drop_tables([TaskEvent])

    resp = client.put(api.url_for(GMan, task_id=task.json['task']['task_id']),
                      json={'message': 'test no table',
                            'status': 'info'})
    assert resp.status_code == 500


def test_failed_event_create_IDK(api, client, monkeypatch, testtask):
    task = testtask()

    def myfunc(*args, **kwargs):
        kwargs['uri'] = {'not a valid thing'}
        return None

    monkeypatch.setattr('piedpiper_gman.orm.models.TaskEvent.create', myfunc)

    resp = client.put(api.url_for(GMan, task_id=task.json['task']['task_id']),
                      json={'message': 'test no table',
                            'status': 'info'})

    assert resp.status_code == 500


def test_gman_post_kwargs(client, api, monkeypatch):
    _post = GMan.post

    def _my_post(*args, **kwargs):
        kwargs['json'] = {
            'run_id': '1_post_task',
            'project': '9435b705-fbca-49a9-a4ab-400cc932bdd1',
            'caller': 'test_post_w_task_id',
            'status': 'started',
            'message': 'Test project is a UUID'}

        return _post(*args, **kwargs)

    monkeypatch.setattr('piedpiper_gman.gman.GMan.post', _my_post)

    resp = client.post(api.url_for(GMan))
    assert resp.status_code == 200
    assert 'timestamp' in resp.json


def test_failed_task_create_no_table(api, client, monkeypatch):

    db.drop_tables([TaskEvent])

    resp = client.post(api.url_for(GMan),
                       json={'run_id': '1_post_task',
                             'project': '9435b705-fbca-49a9-a4ab-400cc932bdd1',
                             'caller': 'test_post_w_task_id',
                             'status': 'started',
                             'message': 'Test project is a UUID'})

    assert resp.status_code == 500
