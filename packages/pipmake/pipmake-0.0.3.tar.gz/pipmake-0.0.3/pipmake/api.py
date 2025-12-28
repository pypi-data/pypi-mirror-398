"""
A python "build backend" defines a three-function API::

     build_wheel()      # invoked by 'pip install' and 'pip wheel'
     build_editable()   # invoked by 'pip install -e'
     build_sdist()      # invoked by 'python -m build --sdist'

FIXME: these functions have arguments ``config_settings`` and ``metadata_directory``
that I haven't figured out yet. (Empirically, these args are ``None`` in typical cases.)

References:

     - https://peps.python.org/pep-0517/
     - https://peps.python.org/pep-0660/
     - https://packaging.python.org/en/latest/specifications/
"""


from .Builder import Builder


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Creates a .whl in 'wheel_directory', and returns the basename.

    This function is part of the python "build backend" API, and is invoked by
    'pip install' and 'pip wheel'.
   
    Reference: https://peps.python.org/pep-0517/#build-wheel
    """
    
    print(f'pipmake: build_wheel() called, {wheel_directory=}')

    builder = Builder(outdir = wheel_directory)
    builder.invoke_makefile('build_wheel')
    builder.read_file_list('wheel_files.txt')
    builder.write_wheel(editable = False)
    
    print(f'pipmake: build_wheel() done')
    return builder.wheel_basename
    
    
def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """Creates a editable .whl in 'wheel_directory', and returns the basename.

    This function is part of the python "build backend" API, and is invoked by
    'pip install -e'.
    
    Reference: https://peps.python.org/pep-0660/#build-editable
    """
    
    print(f'pipmake: build_editable() called, {wheel_directory=}')

    builder = Builder(outdir = wheel_directory)
    builder.invoke_makefile('build_wheel')
    builder.read_file_list('wheel_files.txt')
    builder.write_wheel(editable = True)
    
    print(f'pipmake: build_editable() done')
    return builder.wheel_basename
    

def build_sdist(sdist_directory, config_settings=None):
    """Creates a .tar.gz in 'sdist_directory', and returns the basename.

    This function is part of the python "build backend" API, and is invoked by
    'python -m build --sdist'.
   
    Reference: https://peps.python.org/pep-0517/#build-sdist
    """
    
    print(f'pipmake: build_sdist() called, {sdist_directory=}')

    builder = Builder(outdir = sdist_directory)
    builder.invoke_makefile('build_sdist')
    builder.read_file_list('sdist_files.txt', enforce_package_dir=False)
    builder.write_sdist()
    
    print(f'pipmake: build_sdist() done')
    return builder.sdist_basename
