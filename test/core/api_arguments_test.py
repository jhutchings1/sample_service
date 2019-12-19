import datetime

from pytest import raises
from uuid import UUID
from SampleService.core.api_arguments import datetime_to_epochmilliseconds, get_id_from_object
from SampleService.core.api_arguments import create_sample_params
from SampleService.core.sample import Sample, SampleNode, SubSampleType
from SampleService.core.errors import IllegalParameterError

from core.test_utils import assert_exception_correct


def test_get_id_from_object():
    assert get_id_from_object(None) is None
    assert get_id_from_object({}) is None
    assert get_id_from_object({'id': None}) is None
    assert get_id_from_object({'id': 'f5bd78c3-823e-40b2-9f93-20e78680e41e'}) == UUID(
        'f5bd78c3-823e-40b2-9f93-20e78680e41e')


def test_get_id_from_object_fail_bad_args():
    get_id_from_object_fail({'id': 6}, IllegalParameterError('Sample ID 6 must be a UUID string'))
    get_id_from_object_fail({'id': 'f5bd78c3-823e-40b2-9f93-20e78680e41'}, IllegalParameterError(
        'Sample ID f5bd78c3-823e-40b2-9f93-20e78680e41 must be a UUID string'))


def get_id_from_object_fail(d, expected):
    with raises(Exception) as got:
        get_id_from_object(d)
    assert_exception_correct(got.value, expected)


def dt(t):
    return datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc)


def test_to_epochmilliseconds():
    assert datetime_to_epochmilliseconds(dt(54.97893)) == 54979
    assert datetime_to_epochmilliseconds(dt(-108196017.5496)) == -108196017550


def test_to_epochmilliseconds_fail_bad_args():
    with raises(Exception) as got:
        datetime_to_epochmilliseconds(None)
    assert_exception_correct(got.value, ValueError('d cannot be a value that evaluates to false'))


def test_create_sample_params_minimal():
    params = {'sample': {'version': 7,      # should be ignored
                         'save_date': 9,    # should be ignored
                         'node_tree': [{'id': 'foo',
                                        'type': 'BioReplicate'}]
                         }}
    expected = Sample([SampleNode('foo')])

    assert create_sample_params(params) == (expected, None, None)


def test_create_sample_params_maximal():
    params = {'sample': {'version': 7,      # should be ignored
                         'save_date': 9,    # should be ignored
                         'id': '706fe9e1-70ef-4feb-bbd9-32295104a119',
                         'name': 'myname',
                         'node_tree': [{'id': 'foo',
                                        'type': 'BioReplicate'},
                                       {'id': 'bar',
                                        'parent': 'foo',
                                        'type': 'TechReplicate',
                                        'meta_controlled':
                                            {'concentration/NO2':
                                                {'species': 'NO2',
                                                 'units': 'ppm',
                                                 'value': 78.91,
                                                 'protocol_id': 782,
                                                 'some_boolean_or_other': True
                                                 }
                                             },
                                        'meta_user': {'location_name': {'name': 'my_buttocks'}}
                                        }
                                       ]
                         },
              'prior_version': 1}

    assert create_sample_params(params) == (
        Sample([
            SampleNode('foo'),
            SampleNode(
                'bar',
                SubSampleType.TECHNICAL_REPLICATE,
                'foo',
                {'concentration/NO2':
                    {'species': 'NO2',
                     'units': 'ppm',
                     'value': 78.91,
                     'protocol_id': 782,
                     'some_boolean_or_other': True
                     }
                 },
                {'location_name': {'name': 'my_buttocks'}}
                )
            ],
            'myname'
        ),
        UUID('706fe9e1-70ef-4feb-bbd9-32295104a119'),
        1)


def test_create_sample_params_fail_bad_input():
    create_sample_params_fail(
        None, ValueError('params may not be None'))
    create_sample_params_fail(
        {}, IllegalParameterError('params must contain sample key that maps to a structure'))
    create_sample_params_fail(
        {'sample': {}},
        IllegalParameterError('sample node tree must be present and a list'))
    create_sample_params_fail(
        {'sample': {'node_tree': {'foo', 'bar'}}},
        IllegalParameterError('sample node tree must be present and a list'))
    create_sample_params_fail(
        {'sample': {'node_tree': [], 'name': 6}},
        IllegalParameterError('sample name must be omitted or a string'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'}, 'foo']}},
        IllegalParameterError('Node at index 1 is not a structure'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'type': 'BioReplicate'}, 'foo']}},
        IllegalParameterError('Node at index 0 must have an id key that maps to a string'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'},
                                  {'id': None, 'type': 'BioReplicate'}, 'foo']}},
        IllegalParameterError('Node at index 1 must have an id key that maps to a string'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'},
                                  {'id': 6, 'type': 'BioReplicate'}, 'foo']}},
        IllegalParameterError('Node at index 1 must have an id key that maps to a string'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'},
                                  {'id': 'foo'}, 'foo']}},
        IllegalParameterError('Node at index 1 has an invalid sample type: None'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 6},
                                  {'id': 'foo'}, 'foo']}},
        IllegalParameterError('Node at index 0 has an invalid sample type: 6'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate2'},
                                  {'id': 'foo'}, 'foo']}},
        IllegalParameterError('Node at index 0 has an invalid sample type: BioReplicate2'))
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'},
                                  {'id': 'foo', 'type': 'TechReplicate', 'parent': 6}]}},
        IllegalParameterError('Node at index 1 has a parent entry that is not a string'))

    create_sample_params_meta_fail(6, "Node at index {}'s {} entry must be a mapping")
    create_sample_params_meta_fail(
        {'foo': {}, 'bar': 'yay'},
        "Node at index {}'s {} entry does not have a dict as a value at key bar")
    create_sample_params_meta_fail(
        {'foo': {}, 'bar': {'baz': 1, 'bat': ['yay']}},
        "Node at index {}'s {} entry does not have a primitive type as the value at bar/bat")

    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'},
                                  {'id': 'bar', 'type': 'TechReplicate', 'parent': 'yay'}]}},
        IllegalParameterError('Parent yay of node bar does not appear in node list prior to node.'))

    # the id getting function is tested above so we don't repeat here, just 1 failing test
    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'},
                                  {'id': 'bar', 'type': 'TechReplicate', 'parent': 'bar'}],
                    'id': 'f5bd78c3-823e-40b2-9f93-20e78680e41'}},
        IllegalParameterError(
            'Sample ID f5bd78c3-823e-40b2-9f93-20e78680e41 must be a UUID string'))

    create_sample_params_fail(
        {'sample': {'node_tree': [{'id': 'foo', 'type': 'BioReplicate'},
                                  {'id': 'bar', 'type': 'TechReplicate', 'parent': 'foo'}]},
         'prior_version': 'six'},
        IllegalParameterError('prior_version must be an integer if supplied'))

    


def create_sample_params_meta_fail(m, expected):
    create_sample_params_fail(
        {'sample': {'node_tree': [
            {'id': 'foo', 'type': 'BioReplicate', 'meta_controlled': m}]}},
        IllegalParameterError(expected.format(0, 'controlled metadata')))
    create_sample_params_fail(
        {'sample': {'node_tree': [
            {'id': 'bar', 'type': 'BioReplicate'},
            {'id': 'foo', 'type': 'SubSample', 'parent': 'bar', 'meta_user': m}]}},
        IllegalParameterError(expected.format(1, 'user metadata')))


def create_sample_params_fail(params, expected):
    with raises(Exception) as got:
        create_sample_params(params)
    assert_exception_correct(got.value, expected)