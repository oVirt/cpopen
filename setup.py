from distutils.core import setup, Extension

module1 = Extension('cpopen',
                    sources=['cpopen.c'])

setup(name='cpopen',
      version='1.2.2',
      description='Creates a subprocess in simpler safer manner',
      py_modules=['__init__'],
      author='Yaniv Bronhaim',
      author_email='ybronhei@redhat.com',
      url='redhat.com',
      ext_modules=[module1])
