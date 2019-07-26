import json


def create_request(**kwargs):
    """ Creates json request body from kwargs """

    return json.dumps(kwargs)


def test_hook(test_obj, hook, code, result, **request_kwargs):
    """ Tests the specified hook requesting and returning json response.
    Status code and response body must be the same as specified.

    :param test_obj: Django TestCase object.
    :type test_obj: django.tests.TestCase
    :param hook: URL of the API hook.
    :type hook: str
    :param code: Response status code.
    :type code: int
    :param result: Response json body.
    :type result: dict
    :param request_kwargs: Arguments for request creation.
    :type request_kwargs: kwargs
    """
    response = test_obj.client.post(hook, create_request(**request_kwargs),
                                    content_type="application/json")
    test_obj.assertEqual(response.status_code, code)
    response_data = json.loads(response.content)
    if response_data:
        test_obj.assertEqual(response_data, result)
