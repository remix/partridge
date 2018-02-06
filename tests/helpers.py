import os
from os import path
import zipfile


def fixture(filename):
    """
    Get the handle / path to the test data folder.
    """
    return path.join(path.dirname(__file__), 'fixtures', filename)


def zip_file(scenario):
    """
    Get the file handle / path to the zip file.
    """
    basedir = path.dirname(__file__)
    scenario_dir = path.join(basedir, 'fixtures', scenario)
    scenario_file = path.join(basedir, 'fixtures', scenario + '.zip')

    with zipfile.ZipFile(scenario_file, 'w') as zipf:
        for root, dirs, files in os.walk(scenario_dir):
            for gtfs_file in files:
                zipf.write(path.join(root, gtfs_file), gtfs_file)

    return path.join(basedir, 'fixtures', scenario + '.zip')
