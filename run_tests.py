import sys
import os
import django
import tempfile
import unittest

import balsam

def set_permissions(top):
    os.chmod(top, 0o755)
    for root,subdirs,files in os.walk(top):
        for dir in (os.path.join(root, s) for s in subdirs):
            os.chmod(dir, 0o755)
        for file in (os.path.join(root, f) for f in files):
            os.chmod(file, 0o644)

def main(test_directory):
    
    os.environ['BALSAM_TEST_DIRECTORY'] = test_directory
    os.environ['BALSAM_TEST']='1'
    os.environ['DJANGO_SETTINGS_MODULE'] = 'balsam.django_config.settings'
    django.setup()

    set_permissions(test_directory)

    loader = unittest.defaultTestLoader
    if len(sys.argv) > 1:
        names = sys.argv[1:]
        suite = loader.loadTestsFromNames(names)
    else:
        suite = loader.discover('tests')
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    test_dir = os.path.abspath(os.path.dirname(balsam.__file__))
    tempdir = tempfile.TemporaryDirectory(dir=test_dir, prefix="testdata_")
    main(tempdir.name)
