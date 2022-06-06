import os
import re
from setuptools import setup

#Path of setup file to establish version
setupdir = os.path.abspath(os.path.dirname(__file__))

def find_version(init_file):
	version_file = open(init_file).read()
	version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
	if version_match:
		return version_match.group(1)
	else:
		raise RuntimeError("Unable to find version string.")

#Readme from git
def readme():
	with open('README.md') as f:
		return f.read()

setup(name='plotannot',
		version=find_version(os.path.join(setupdir, "plotannot", "__init__.py")),	#get version from __init__.py
		description='',
		long_description=readme(),
		long_description_content_type='text/markdown',
		url='https://github.com/msbentsen/plotannot',
		author='Mette Bentsen',
		author_email='mette.bentsen@mpi-bn.mpg.de',
		license='MIT',
		packages=["plotannot"],
		install_requires=[
			'matplotlib',
			'numpy',
		],
		classifiers=[
			'License :: OSI Approved :: MIT License',
			'Intended Audience :: Science/Research',
			'Topic :: Scientific/Engineering :: Visualization',
			'Programming Language :: Python :: 3'
		],
)