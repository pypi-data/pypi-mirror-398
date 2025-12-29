from setuptools import setup
from setuptools.dist import Distribution


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""
    def has_ext_modules(self):
        return True


try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # Force manylinux platform tag
            self.plat_name_supplied = True
            self.plat_name = 'manylinux_2_17_x86_64'

    cmdclass = {'bdist_wheel': bdist_wheel}
except ImportError:
    cmdclass = {}


setup(
    distclass=BinaryDistribution,
    cmdclass=cmdclass,
)
