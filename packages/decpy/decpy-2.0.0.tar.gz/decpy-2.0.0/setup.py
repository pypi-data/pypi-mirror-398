from setuptools import setup, find_packages


def readme():
  with open('README.md', 'r') as f:
    return f.read()


setup(
  name='decpy',
  version='2.0.0',
  author='Paul Dobryak',
  author_email='goodsoul@mail.ru',
  description='Declarative Programming Tools',
  long_description=readme(),
  long_description_content_type='text/markdown',
  url='https://github.com/pauldobriak/DecPy',
  packages=find_packages(),
  project_urls={
    'GitHub': 'https://github.com/pauldobriak/DecPy'
  }
)
