from setuptools import setup

setup(name='otpdoor',
      description='OTPdoor is a Python library for creating and managing OTP (One-Time Password) authentication with nginx.',
      url='https://github.com/germanespinosa/otpdoor',
      author='German Espinosa',
      author_email='germanespinosa@gmail.com',
      long_description=open('./otpdoor/README.md').read() + '\n---\n<small>Package created with Easy-pack</small>\n',
      long_description_content_type='text/markdown',
      packages=['otpdoor'],
      install_requires=['pyotp', 'requests', 'flask', 'cryptography'],
      license='MIT',
      include_package_data=True,
      version='0.0.3',
      zip_safe=False)
