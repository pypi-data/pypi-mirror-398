import sys
import os
import shutil
import glob
from subprocess import run


def build(temp_dir, output_dir, plugin_name, plugin_version="0.0.1"):
    create_setup_file(temp_dir, plugin_name, plugin_version)
    compile_plugin(temp_dir, output_dir)
    print('Done.')


##########################################################################

def create_setup_file(temp_dir, plugin_name, plugin_version):
    setup_file_content = """
from setuptools import setup
from setuptools.dist import Distribution


PYTHON_VERSION = (3,8)
class BinaryDistribution(Distribution):
    #Distribution which always forces a binary package with platform name
    def has_ext_modules(foo):
        return True


options = dict(
    name='onetick.query_webapi.{plugin_name}',
    packages=[
        'onetick.query_webapi.plugin.{plugin_name}',
        'onetick.query_webapi.plugin.{plugin_name}.ep'
    ],

    version='{version}',
    description='OneTick client package',
    long_description=__doc__,
    author='OneTick',
    author_email='support@onetick.com',
    url='https://www.onetick.com',
    license='commercial',

    zip_safe=True,
    include_package_data=True,

    entry_points={{
        'onetick.query_webapi.plugin': 'onetick.query_webapi.{plugin_name} = onetick.query_webapi.plugin.{plugin_name}'
    }},
    install_requires=[
        'onetick.query_webapi',
    ],
)

#########################
if __name__ == '__main__':
    setup(**options)
""".format(plugin_name=plugin_name, version=plugin_version)

    setup_file = temp_dir + '/setup.py'
    f = open(setup_file, "x")
    f.write(setup_file_content)
    f.close()


def compile_plugin(temp_dir, output_dir):
    print('create Wheel binary distribution...')

    os.chdir(temp_dir)
    cmd = f'{sys.executable} setup.py bdist_wheel'
    run(cmd.split())
    whl_file = temp_dir + '/dist/*.whl'
    for file in glob.glob(whl_file):
        shutil.copy(file, output_dir)
