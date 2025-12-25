from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='aanalyticsact-1',
    version='0.0.2.1',
    long_description    = long_description,
    long_description_content_type='text/markdown',
    description='adobe analytics library for Team ACT',
    license             = 'MIT',
    author='Youngkwang Cho',
    author_email='youngkwang.cho@concentrix.com',
    url='https://github.com/YK124/Glory-s',
    install_requires=['aanalytics2', 'pymysql', 'aanalyticsactauth','pandas'],
    packages=find_packages(exclude=[]),
    keywords=['adobe','analytics','api'],
    python_requires='>=3.6',
    package_data={},
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',

    ],
)
