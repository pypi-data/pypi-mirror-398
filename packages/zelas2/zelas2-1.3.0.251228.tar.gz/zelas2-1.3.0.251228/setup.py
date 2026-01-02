import codecs
import os
from setuptools import setup, find_packages
# these things are needed for the README.md show on pypi (if you do not need delete it)
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
 long_description = "\n" + fh.read()
# you need to change all these
VERSION = '1.3.0.251228'
DESCRIPTION = 'a ligh weight menu , support both win and mac '
LONG_DESCRIPTION = 'dumb_menu is a ligh weight menu ,support hot key, support both win and mac'
setup(
 name="zelas2",
 version=VERSION,
 author="Ze You, Shichao Wang, Huaxin Chen, Yimo Geng, Yuqing Wang, Jun Wang",
 author_email="youze1997@163.com",
 description=DESCRIPTION,
 long_description_content_type="text/markdown",
 long_description=long_description,
 packages=find_packages(),
 install_requires=[],
 keywords=['python', 'menu', 'dumb_menu','windows','mac','linux'],
 classifiers=[
 "Development Status :: 1 - Planning",
 "Intended Audience :: Developers",
 "Programming Language :: Python :: 3",
 "Operating System :: Unix",
 "Operating System :: MacOS :: MacOS X",
 "Operating System :: Microsoft :: Windows",
 ]
)