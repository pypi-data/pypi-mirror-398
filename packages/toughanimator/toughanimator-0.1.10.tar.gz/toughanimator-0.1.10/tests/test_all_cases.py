import os
import json
import pytest
#from toughanimator.tough_classes import VisSetting, vis_reader
import logging
import toughanimator as ta
import shutil

logging.basicConfig(level=logging.DEBUG)

# Directory containing all test cases
parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_CASES_DIRS = [
    os.path.join(parent_path, "test_cases"),
    #os.path.join(parent_path, "unresolved"),
    ]


def discover_test_cases():
    """
    Discover all test cases and load configurations.
    Each test case must have a config.json file.
    """
    logging.debug("This is a debug log")
    cases = []
    for test_cases_dir in TEST_CASES_DIRS:
        logging.debug(f"cases_dir: {test_cases_dir}")
        if os.path.exists(test_cases_dir):
            for case_name in os.listdir(test_cases_dir):
                logging.debug(f"case_name: {case_name}")
                case_dir = os.path.join(test_cases_dir, case_name)
                cases.append((case_name, case_dir))
    return cases


@pytest.mark.parametrize("case_name, case_dir", discover_test_cases())
def test_toughanimator_case(case_name, case_dir):
    """
    Test each case using its configuration file.
    """
    print(f"Running test for case: {case_name}")



    try:
        # Execute the process
        reader = ta.vis_reader(case_dir)
        #reader.write_geometry()
        #reader.write_incon()
        #reader.write_result()
        reader.write_all()
        vis_path = os.path.join(case_dir, "tough_vis")
        # delete the directory if it exists
        if os.path.isdir(vis_path):
            shutil.rmtree(vis_path)

            
        
        assert True  # If no exceptions, the test passes
    except Exception as e:
        pytest.fail(f"Test failed for case {case_name}: {e}")
