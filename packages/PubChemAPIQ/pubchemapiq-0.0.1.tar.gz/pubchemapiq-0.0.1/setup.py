from setuptools import setup, find_packages

# Read long description safely
with open("README.md", "r", encoding="utf-8") as fh:
    long_desc = fh.read()

try:
    with open("CHANGELOG.txt", "r", encoding="utf-8") as ch:
        long_desc += "\n\n" + ch.read()
except FileNotFoundError:
    pass  # Optional: skip if CHANGELOG.txt not present

# Classifiers
classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'Operating System :: OS Independent',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
    'Topic :: Scientific/Engineering :: Chemistry'
]

setup(
    name='PubChemAPIQ',
    version='0.0.1',  # Increment version for each upload
    description='Simplifies interaction with the PubChem database via PUG-REST API.',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    url='https://github.com/ahmed1212212/PubChemAPIQ',
    author='Ahmed Alhilal',
    author_email='aalhilal@kfu.edu.sa',
    license='MIT',
    classifiers=classifiers,
    keywords='cheminformatics pubchem api biology chemistry drug-discovery',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.0'
    ],
    project_urls={
        'Source': 'https://github.com/ahmed1212212/PubChemAPIQ',
        'Tracker': 'https://github.com/ahmed1212212/PubChemAPIQ/issues',
    },
    python_requires='>=3.7',
)
