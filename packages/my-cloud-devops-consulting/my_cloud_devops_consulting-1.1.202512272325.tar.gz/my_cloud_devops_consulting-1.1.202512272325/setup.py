from setuptools import setup, find_packages
from datetime import datetime

setup(
    name='my_cloud_devops_consulting',
    version=datetime.now().strftime("1.1.%Y%m%d%H%M"),  # auto-version like 1.1.202503241130
    author='Betrand Mutagha',
    author_email='mmutagha@gmail.com',
    description='This is my consulting website for Cloud & DevOps services.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Betrand1999/project-root',
    packages=find_packages(where="."),
    py_modules=["app"],
    include_package_data=True,
    package_data={
        "": ["static/**/*", "templates/**/*"],
    },
    install_requires=[
        'Flask>=2.0',
        'pymongo',
        'werkzeug',
        'requests',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
