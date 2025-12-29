from setuptools import setup, find_packages

def readme():

  with open('README.md', 'r') as f:
    return f.read()

setup(
    name="brief_survey",
    version="0.2.10.1",
    description="Dynamic survey/dialog for aiogram3  with aiogram_dialog and Pydantic support",
    author="Fugguri",
    url="https://github.com/Fugguri/brief_survey",
    packages=find_packages(),
    long_description_content_type='text/markdown',
    long_description=readme(),
    classifiers=[
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    install_requires=[

        "aiogram>=3.20",
        "aiogram_dialog>=2.3.1",
        "phonenumbers>=9.0.10",
        "pydantic>=2.11.7",
        "humanfriendly>=10.0",
    ],
    keywords='aiogram3,aiogram, aiogram_dialog, brief  ',
    project_urls={
        'pypi': 'https://pypi.org/project/brief-survey/',
        'github':'https://github.com/Fugguri/brief_survey'
    },
    python_requires='>=3.12',

)
