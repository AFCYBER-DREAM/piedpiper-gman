import uuid

import pytest

from piedpiper_gman.gman import GMan

# from piedpiper_gman.orm.models import (Task, TaskEvent,
#                                        TaskSchema, TaskEventSchema)


# '(object_to_json,
#   expected resp_code,
#   ((test_assertion_func, 'assertion_failed because'),)'
gman_task_create_post = [
    # ({'run_id': '123',
    #   'project': 'abc123',
    #   'caller': 'testFaasFunc',
    #   'status': 'started',
    #   'message': 'test this functions start'},
    #  201,
    #  ((lambda x: 'task_id' in x, 'Missing "task_id"'),
    #   (lambda x: uuid.uuid(x['task_id']), 'Invalid "task_id" UUID')),
    #
    #  ({'run_id': '123',
    #    'project': 'abc123',
    #    'caller': 'testFaasFunc',
    #    'message': 'test this functions start'},
    #   201),
    #  ((lambda x: 'task_id' in x, 'Missing "task_id"'),
    #   (lambda x: uuid.uuid(x['task_id']), 'Invalid "task_id" UUID')),
    #  ({'run_id': 'ba279fdc-e11d-4bc8-828c-a44e35b55175',
    #    'project': 'abc123',
    #    'caller': 'testFaasFunc',
    #    'status': 'info',
    #    'message': 'test this functions start'},
    #   400,
    #   ((lambda x: 'error' in x, 'No error message returned'),
    #    (lambda x: x['errors'] == ('Task creation requires status: started'
    #                              'or status: undef'),
    #     'Task allowed status other then started for a creation event'))),
    #  ({'run_id': 'ba279fdc-e11d-4bc8-828c-a44e35b55175',
    #    'task_id': 'ba279fdc-e11d-4bc8-828c-a44e35b55175',
    #    'project': 'abc123',
    #    'caller': 'testFaasFunc',
    #    'message': 'test this functions start'},
    #   422,
    #   ((lambda x: 'errors' in x, 'No error message returned'),
    #    (lambda x: x['error'] == 'task_id specified on a post/create',
    #     'Task creation allowed a defined task_id'))),
     ({'blah': '12345',
       'task_id': 'ba279fdc-e11d-4bc8-828c-a44e35b55175',
       'project': 'abc123',
       'caller': 'testFaasFunc',
       'message': 'testing random fields'},
      422,
      ((lambda x: 'errors' in x, 'No error message returned'),
       (lambda x: 'task_id specified on a post/create' in x['error'],
        'Task creation allowed specified task_id'
        )))]


@pytest.mark.parametrize("data,resp_code,tests", gman_task_create_post)
def test_gman_post(data, resp_code, tests, api, client):
    resp = client.post(api.url_for(GMan), json=data)

    assert resp.status_code == resp_code, f'Invalid response code {resp_code}'

    for test in tests:
        assert test[0](resp.json), test[1]
