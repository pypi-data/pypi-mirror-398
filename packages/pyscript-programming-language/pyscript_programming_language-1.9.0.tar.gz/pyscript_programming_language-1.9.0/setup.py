from setuptools import find_packages, setup

with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='pyscript-programming-language',
    version='1.9.0',
    description='PyScript Programming Language',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='azzammuhyala',
    author_email='azzammuhyala@gmail.com',
    url='https://azzammuhyala.github.io/pyscript',
    project_urls={
        'Source': 'https://github.com/azzammuhyala/pyscript',
        'Bug Tracker': 'https://github.com/azzammuhyala/pyscript/issues'
    },
    extras_require={
        'extras': ['beartype', 'pygments']
    },
    license='MIT',
    python_requires='>=3.10',
    packages=find_packages(),
    include_package_data=True,
    keywords=['pyscript', 'pyslang', 'pys', 'programming', 'language', 'programming language'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Compilers',
    ]
)