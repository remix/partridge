import os
import shutil


fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture(filename):
    """
    Get the handle / path to the test data folder.
    """
    return os.path.join(fixtures_dir, filename)


def zip_file(scenario):
    """
    Get the file handle / path to the zip file.
    """
    scenario_dir = os.path.join(fixtures_dir, scenario)
    return shutil.make_archive(scenario_dir, "zip", scenario_dir)
