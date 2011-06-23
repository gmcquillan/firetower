from setuptools import find_packages, setup

setup(name="Firetower",
      version="dev",
      packages=find_packages(),
      namespace_packages=['firetower'],
      include_package_data=True,
      author='Gavin McQuillan',
      author_email='gavin.mcquillan@gmail.com',
      description='Prototype Error Aggregation and Classification System',
      long_description='',
      zip_safe=False,
      platforms='any',
      license='MIT',
      url='https://github.com/gmcquillan/firetower',
      classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Education',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Operating System :: Unix',
        ],

      install_requires=[
        'python-Levenshtein',
        ],
      )
