from setuptools import setup

setup(
    name='crew-cli',
    version='1.0.0',
    py_modules=['crew', 'crew_utils'],
    install_requires=[
        # No external dependencies yet, but we could add 'requests' later
    ],
    entry_points={
        'console_scripts': [
            'crew = crew:main',
        ],
    },
    author='127 Crew',
    description='A Package Manager for C/C++',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/127crew/crewpackagemanager',
    license='GPL-3.0',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Build Tools',
        'Intended Audience :: Developers',
    ],
    python_requires='>=3.6',
)
