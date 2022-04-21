from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='Shimeji',
    description='Shimeji is a framework to create GPT-powered chatbots.',
    version='0.1.0',
    license='GPLv2',
    author='Hitomi-Team',
    url='https://github.com/hitomi-team/shimeji',
    packages=['shimeji'],
    install_requires=required
)
