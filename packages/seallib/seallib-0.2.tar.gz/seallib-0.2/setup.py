from setuptools import setup, find_packages

setup(
    name='seallib',
    version='0.2',
    packages=find_packages(),
    author='Yaroslav Merkulov',
    author_email='1132242913@rudn.ru',
    description='Учебная библиотека',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    license='MIT',
    keywords='example library python',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ]
)