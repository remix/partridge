import os
import shutil


def fixture(filename):
    """
    Get the handle / path to the test data folder.
    """
    return os.path.join(os.path.dirname(__file__), 'fixtures', filename)


def zip_file(scenario):
    """
    Get the file handle / path to the zip file.
    """
    fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenario_dir = os.path.join(fixture_dir, scenario)
    return shutil.make_archive(scenario_dir, 'zip', scenario_dir)
