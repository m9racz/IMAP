from setuptools import setup, find_packages
with open('README.md') as f:
    readme = f.read()
setup(
    name='MyLibrary',
    version='0.0.1',
    description='IMAP tester for IW server',
    long_description=readme,
    author='Miroslav Bambas',
    author_email='miroslav.bambas@email.cz',
    url='https://github.com/m9racz/IMAP.git',
    license=license,
    packages=find_packages()
)