import jupygrader
import os

def test_grade_notebook():
    TEST_NOTEBOOKS_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'test-notebooks',
    )

    TEST_OUTPUT_DIR = os.path.join(
        TEST_NOTEBOOKS_DIR,
        'test-output',
    )

    notebook_path = os.path.join(TEST_NOTEBOOKS_DIR, 'test-file.ipynb')

    result = jupygrader.grade_notebook(
        notebook_path=notebook_path,
        output_path=TEST_OUTPUT_DIR,
    )
    print(result)

    # Check the accuracy of the result object
    assert result['filename'] == 'test-file.ipynb'
    assert result['learner_autograded_score'] == 55
    assert result['max_autograded_score'] == 60
    assert result['max_manually_graded_score'] == 10
    assert result['max_total_score'] == 70
    assert result['num_total_test_cases'] == 7
    assert result['num_passed_cases'] == 5
    assert result['num_failed_cases'] == 1
    assert result['num_autograded_cases'] == 6
    assert result['num_manually_graded_cases'] == 1

    # Check that results contains a list of 6 items
    assert 'results' in result
    assert isinstance(result['results'], list)
    assert len(result['results']) == 7

    # Check that each result item contains all required keys
    required_keys = {
        'test_case_name',
        'points',
        'available_points',
        'pass',
        'grade_manually',
        'message'
    }

    for test_result in result['results']:
        # Check that all required keys exist
        assert set(test_result.keys()).issuperset(required_keys), \
            f"Missing required keys in test result. Expected keys: {required_keys}"
        
        # Check types of values
        assert isinstance(test_result['test_case_name'], str)
        assert isinstance(test_result['points'], (int, float))
        assert isinstance(test_result['available_points'], (int, float))
        assert isinstance(test_result['pass'], bool) or test_result['pass'] is None
        assert isinstance(test_result['grade_manually'], bool)
        assert isinstance(test_result['message'], str)