from setuptools import setup

setup(
    name='Impression-CMS',
    version='0.2.0',
    url='https://smeggingsmegger.github.io/impression/',
    author='Scott Blevins',
    author_email='sblevins@gmail.com',
    packages=['impression'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'flask',
        'Flask-Assets',
        'Flask-Cache',
        'Flask-Login',
        'Flask-Mail',
        'Flask-Migrate',
        'Flask-Permissions',
        'Flask-Script',
        'Flask-SQLAlchemy',
        'Flask-Themes2',
        'Flask-WTF',
        'simplejson',
        'textile',
        'python-creole',
        'Markdown',
        'pillow',
        'python-dateutil',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points='''
        [console_scripts]
        impression=impression.runserver:main
    ''',
)
