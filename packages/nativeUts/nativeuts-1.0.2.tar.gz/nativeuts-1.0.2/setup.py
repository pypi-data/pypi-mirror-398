from setuptools import setup, find_packages, Extension
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='nativeUts',
  version='1.0.2',
  description='A Python package for native utilities.',
  long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.txt').read(),
  long_description_content_type='text/markdown',
  url='',  
  author='Melque Lima',
  author_email='melque_ex@yahoo.com.br',
  license='MIT', 
  classifiers=classifiers,
  keywords='nativeUts', 
  packages=find_packages(),
  install_requires=[
      'forbiddenfruit==0.1.4',
  ]
)
