# Jupygrader Before File Code
# REMOVE_IN_HTML_OUTPUT
import datetime

grading_start_time = datetime.datetime.now(datetime.timezone.utc)

_graded_result = {
    'filename': None,
    'learner_autograded_score': 0,
    'max_autograded_score': 0,
    'max_manually_graded_score': 0,
    'max_total_score': 0,
    'num_autograded_cases': 0,
    'num_passed_cases': 0,
    'num_failed_cases': 0,
    'num_manually_graded_cases': 0,
    'num_total_test_cases': 0,
    'grading_finished_at': None,
    'grading_duration_in_seconds': 0,
    'results': [],
}

is_jupygrader_env = True

def _record_test_case(test_case_name, did_pass, available_points, message='', grade_manually=False):
    global _graded_result
    warning_message = ''
    
    if test_case_name in map(lambda x: x['test_case_name'], _graded_result['results']):
        warning_message = f'[Warning] Jupygrader: An identical test case name "{test_case_name}" already exists. Test cases with identical test case names will be graded \n\n'

    _graded_result['results'].append({
        'test_case_name': test_case_name,
        'points': available_points if did_pass else 0,
        'available_points': available_points,
        'pass': did_pass,
        'grade_manually': grade_manually,
        'message': warning_message + message,
    })

import unittest

tc = unittest.TestCase()

my_var = 1

my_another_var = 3

# Jupygrader After File Code
# REMOVE_IN_HTML_OUTPUT
import json
import datetime

grader_output_file_name = 'jupygrader-result.json'
grading_end_time = datetime.datetime.now(datetime.timezone.utc)

_graded_result['grading_finished_at'] = grading_end_time.strftime("%Y-%m-%d %I:%M %p %Z")
_graded_result['grading_duration_in_seconds'] = round((grading_end_time - grading_start_time).total_seconds(), 2)
_graded_result['num_total_test_cases'] = len(_graded_result['results'])

for test_case_result in _graded_result['results']:
    _graded_result['learner_autograded_score'] += test_case_result['points']
    _graded_result['max_total_score'] += test_case_result['available_points']
    
    if test_case_result['grade_manually']:
        _graded_result['max_manually_graded_score'] += test_case_result['available_points']
        _graded_result['num_manually_graded_cases'] += 1
    else:
        _graded_result['max_autograded_score'] += test_case_result['available_points']
        _graded_result['num_autograded_cases'] += 1
        
        if test_case_result['pass']:
            _graded_result['num_passed_cases'] += 1
        else:
            _graded_result['num_failed_cases'] += 1
    
with open(grader_output_file_name, 'w') as fp:
    json.dump(_graded_result, fp, indent=2)

