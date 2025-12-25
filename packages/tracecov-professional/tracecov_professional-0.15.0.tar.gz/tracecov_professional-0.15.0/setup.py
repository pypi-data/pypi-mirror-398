import sys

from setuptools import setup
from setuptools.command.install import install


class BlockInstall(install):
    def run(self):
        sys.stderr.write(
            "\nERROR: 'tracecov-professional' is not available on PyPI.\n"
            "Contact info@tracecov.sh for access.\n"
        )
        sys.exit(1)


setup(
    name="tracecov-professional",
    version="0.15.0",
    description="TraceCov Professional Edition. Contact info@tracecov.sh for access.",
    packages=[],
    cmdclass={"install": BlockInstall},
    zip_safe=False,
)
