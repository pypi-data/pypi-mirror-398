from pathlib import Path
from setuptools import find_packages, setup

def read_requirements(filename: str):
    return [line.strip() for line in Path(filename).read_text().splitlines() if line.strip() and not line.startswith("#")]

root                    = Path(__file__).resolve().parent
production_requirements = (root / 'requirements.txt').read_text().splitlines()
extra_requirements      = (root / 'requirements.dev.txt').read_text().splitlines()

setup(
    name='espark-core',
    version='0.5.3',
    description='The core module of the Espark ESP32-based IoT device management framework.',
    long_description=(root / 'README.md').read_text(),
    long_description_content_type='text/markdown',
    license='MIT',
    license_files=[
        'LICENSE',
    ],
    python_requires='>=3.8',
    packages=find_packages(where='.'),
    package_dir={
        '' : '.',
    },
    install_requires=production_requirements,
    extras_require={
        'dev' :  extra_requirements,
    },
)
