# zernikepolpy

zernikepolpy is an open source ([MIT](#License)) pure Python library for
calculations with Zernike Polynoms.

## Build package

### prepare build process

module build is needed to create wheel, module twine is needed to publish on PyPi
pip install build
pip install twine

### create wheel
python -m build

creates for example:

  dist/zernike-0.0.1-py3-none-any.whl
  dist/zernike-0.0.1.tar.gz

### versions

 major.minor.patch.test

 major = major version of software; starting with 0; increased due to large changes in software
 minor = minor version of software; starting with 1; increased with every release; set to 1 when major is changed
 patch = patch level of software; starting with 0 (=release of minor version); increased with every bugfix; set to 0 when minor is changed
 test = number of test upload to testpypi; shall never appear in any release

## License

zernikepolpy is released under the MIT license, hence allowing commercial use of
the library. Please refer to the [COPYING] file.
