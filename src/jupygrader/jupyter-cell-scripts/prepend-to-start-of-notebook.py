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
        'did_pass': did_pass,
        'grade_manually': grade_manually,
        'message': warning_message + message,
    })