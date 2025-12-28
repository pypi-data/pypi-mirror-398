from setuptools import setup, find_packages

# to deploy the package to PyPI, run the following command:
# pip install setuptools wheel twine
# python setup.py sdist bdist_wheel
# twine upload dist/*

setup(
    name='kolzchut-ragbot',
    version='1.17.12',
    author='Shmuel Robinov',
    author_email='shmuel_robinov@webiks.com',
    description='A search engine using machine learning models and Elasticsearch for advanced document retrieval.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/shmuelrob/rag-bot',
    packages=find_packages(),
    install_requires=[
        'elasticsearch==8.17.1',
        'sentence-transformers==3.4.1',
        'torch==2.6.0',
        'transformers==4.48.3'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
