import os
import zipfile

def fixture(filename):
    """
    Get the handle / path to the test data folder.
    """
    return os.path.join(os.path.dirname(__file__), 'fixtures', filename)


def zip_file(scenario):
    """
    Get the file handle / path to the zip file.
    """
    scenario_dir = os.path.join(os.path.dirname(__file__), 'fixtures', scenario)
    scenario_file = os.path.join(os.path.dirname(__file__), 'fixtures', scenario + '.zip')
    with zipfile.ZipFile(scenario_file, 'w') as zipf:
        for root, dirs, files in os.walk(scenario_dir):
            for gtfs_file in files:
                zipf.write(os.path.join(root, gtfs_file), gtfs_file)
    return os.path.join(os.path.dirname(__file__), 'fixtures', scenario + '.zip')
