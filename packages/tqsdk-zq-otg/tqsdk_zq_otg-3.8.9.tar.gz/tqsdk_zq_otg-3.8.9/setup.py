# -*- coding: utf-8 -*-
__author__ = 'chenli'

import setuptools

# from py-spy/setup.py
try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):

        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package (we have platform specific lib)
            if self.plat_name != "any":
                self.root_is_pure = False
                self.distribution.package_data[""] = ["zq_otg/*", "zq_otg/**/*"]

        def get_tag(self):
            # this set's us up to build generic wheels.
            python, abi, plat = _bdist_wheel.get_tag(self)
            # We don't contain any python source
            python, abi = 'py3', 'none'
            return python, abi, plat
except ImportError:
    bdist_wheel = None

setuptools.setup(
    name='tqsdk_zq_otg',
    version="3.8.9",
    description='TianQin SDK - zq_otg lib',
    author='TianQin',
    author_email='tianqincn@gmail.com',
    url='https://www.shinnytech.com/tqsdk',
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3',
    cmdclass={'bdist_wheel': bdist_wheel},
    install_requires=["tqsdk==3.8.9"],
)
