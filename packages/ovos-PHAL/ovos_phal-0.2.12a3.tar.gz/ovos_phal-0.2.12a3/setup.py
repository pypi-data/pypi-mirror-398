import os
from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    """ Find the version of the package"""
    version = None
    version_file = os.path.join(BASEDIR, 'ovos_PHAL', 'version.py')
    major, minor, build, alpha = (None, None, None, None)
    with open(version_file) as f:
        for line in f:
            if 'VERSION_MAJOR' in line:
                major = line.split('=')[1].strip()
            elif 'VERSION_MINOR' in line:
                minor = line.split('=')[1].strip()
            elif 'VERSION_BUILD' in line:
                build = line.split('=')[1].strip()
            elif 'VERSION_ALPHA' in line:
                alpha = line.split('=')[1].strip()

            if ((major and minor and build and alpha) or
                    '# END_VERSION_BLOCK' in line):
                break
    version = f"{major}.{minor}.{build}"
    if alpha and int(alpha) > 0:
        version += f"a{alpha}"
    return version


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


long_description = ""
if os.path.isfile(os.path.join(BASEDIR, "README.md")):
    with open(os.path.join(BASEDIR, "README.md"), "r") as f:
        long_description = f.read()


setup(
    name='ovos_PHAL',
    version=get_version(),
    packages=['ovos_PHAL'],
    install_requires=required("requirements/requirements.txt"),
    extras_require={
        "extras": required("requirements/extras.txt"),
        "linux": required("requirements/linux.txt"),
        "mac": required("requirements/mac.txt"),
        "mk1": required("requirements/mk1.txt"),
        "mk2": required("requirements/mk2.txt"),
        "mk2dev": required("requirements/mk2dev.txt")
    },
    package_data={'': package_files('ovos_PHAL')},
    url='https://github.com/OpenVoiceOS/ovos-PHAL',
    description="Plugin based Hardware Abstraction Layer for OVOS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='apache-2.0',
    author='jarbasAi',
    author_email='jarbasai@mailfence.com',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'ovos_PHAL=ovos_PHAL.__main__:main',
            'ovos_PHAL_admin=ovos_PHAL.admin:main'
        ]
    }
)
