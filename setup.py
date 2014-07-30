from distutils.core import setup, Extension

ext_modules = [Extension('cpopen.cpopen',
                         sources=['cpopen/cpopen.c'])]

setup(name='cpopen',
      version='1.3-4',
      description='Creates a subprocess in simpler safer manner',
      license="GNU GPLv2+",
      author='Yaniv Bronhaim',
      author_email='ybronhei@redhat.com',
      url='redhat.com',
      packages=['cpopen'],
      ext_modules=ext_modules)
