from setuptools import setup, find_packages
import os


BASEDIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    version_file = os.path.join(BASEDIR, 'ovos_yaml_editor', 'version.py')
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
    if int(alpha):
        version += f"a{alpha}"
    return version


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]



setup(
    name="ovos-yaml-editor",
    version=get_version(),
    description="Simple YAML editor for OpenVoiceOS with FastAPI backend",
    url="https://github.com/OpenVoiceOS/ovos-yaml-editor",
    packages=find_packages(),
    install_requires=required('requirements.txt'),
    entry_points={
        "console_scripts": [
            "ovos-yaml-editor = ovos_yaml_editor:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
