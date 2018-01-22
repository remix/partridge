import os
import zipfile

def fixture(filename):
    return os.path.join(os.path.dirname(__file__), 'fixtures', filename)


def zip_file(scenario):
    scenario_dir = os.path.join(os.path.dirname(__file__), 'fixtures', scenario)
    scenario_file = os.path.join(os.path.dirname(__file__), 'fixtures', scenario + '.zip')
    with zipfile.ZipFile(scenario_file, 'w') as zipf:
        for root, dirs, files in os.walk(scenario_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    return os.path.join(os.path.dirname(__file__), 'fixtures', scenario + '.zip')
