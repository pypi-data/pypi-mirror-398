from setuptools import setup, find_packages

setup(name='SHICTHRSCSVLoader',
      version='1.5.0',
      description='SHICTHRS CSV file io system',
      url='https://github.com/JNTMTMTM/SHICTHRS_CSVLoader',
      author='SHICTHRS',
      author_email='contact@shicthrs.com',
      license='GPL-3.0',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['colorama==0.4.6' , 'pandas==2.3.3'],
      zip_safe=False)
