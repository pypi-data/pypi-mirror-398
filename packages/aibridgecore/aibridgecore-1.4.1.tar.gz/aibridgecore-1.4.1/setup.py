import io
import os
import sys
from shutil import rmtree
from setuptools import find_packages, setup, Command

NAME = "aibridgecore"
DESCRIPTION = 'Bridge for LLM"s'
URL = "https://github.com/23ventures/aibridge-core"
EMAIL = "developer.tools@23v.co"
AUTHOR = "Ashish Tilekar"
REQUIRES_PYTHON = ">=3.9.0"
VERSION = "1.4.1"
REQUIRED = [
    "openai<=1.82.1",
    "SQLAlchemy>=2.0.19",
    "redis>=4.6.0",
    "PyYAML>=6.0.1",
    "Jinja2>=3.1.2",
    "pymongo>=4.4.1",
    "sqlparse>=0.4.4",
    "jsonschema>=4.18.4",
    "Pillow>=10.0.0",
    "google-genai>=1.2.0",
    "cohere>=5.13.11",
    "ai21>=2.13.0",
    "xmltodict>=0.13.0",
    "anthropic>=0.45.2",
    "ollama<=1.2.2",
]

here = os.path.abspath(os.path.dirname(__file__))
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

about = {}
about["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Publishing the AIBRIDGE1"
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=[]),
    install_requires=REQUIRED,
    include_package_data=True,
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
