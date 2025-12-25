from setuptools import setup, find_packages
import os

if __name__ == "__main__":
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    setup(
        packages=find_packages(where='./src'),
        package_data={
            "feathersdk": ["**/*.c", "**/*.h", "**/*.eds"],
        },
        long_description=open(readme_path).read(),
        long_description_content_type='text/markdown',
        install_requires=[
            'canopen',
            'typing_extensions',
            'filelock',
            'numpy',
            'psutil',
            'smbus2',
            'hydra-core',
        ],
    )