# Copyright 2025 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===========================================================================
import sys
import setuptools

readme = """
*WARNING*:This project is not functional and is a placeholder form HUAWEI Ascend
Please refer to homepage https://gitcode.com/Ascend/MindIE-Motor
"""

setuptools.setup(
    name='mindie-motor',
    version='0.0.1.dev1',
    description='inference cluster management',
    url='https://gitcode.com/Ascend/MindIE-Motor',
    long_description_content_type="text/markdown",
    long_description=readme,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent'
    ],
    license='Apache',
    python_requires='>= 3.7',
    include_package_data=True
)

if len(sys.argv) !=2 or sys.argv[1] != "sdist":
    raise ValueError(readme)
