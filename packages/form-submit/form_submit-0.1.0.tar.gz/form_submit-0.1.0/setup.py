
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='form_submit',
    version='0.1.0',
    author='Louati Mahdi',
    author_email='louatimahdi390@gmail.com',
    description='A Python package to display an HTML form in Colab, capture submissions, and send data via email.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mahdi123-tech/form_submit',
    packages=find_packages(),
    install_requires=[
        'ipython',
        'requests',
        'oauth2client',
        'google-api-python-client'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Framework :: IPython',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.7',
)
