"""
pipmake: A trivial python "build backend" that delegates to a Makefile.
This allows builds to be entirely controlled by 'make', but fully integrated with pip/pypi/etc.

  - The Makefile defines a target ``make build_wheel``, which creates a file
    ``wheel_files.txt`` containing filenames to be installed with ``pip install``
    (one filename per line).

    The file ``wheel_files.txt`` contains python source files (`.py`), compiled 
    extension modules (`.so`), and any auxiliary files needed by the `(.py,.so)` files.

    **The 'make build_wheel' target must fully build all files listed in 'wheel_files.txt'.**

  - If you'd like to create "sdists" (e.g. for uploading to PyPI), then the Makefile
    must define a target ``make build_sdist``, which creates a file containing source
    filenames to be included in the sdist.

    The file ``sdist_files.txt`` usually contains ``pyproject.toml``, ``Makefile``,
    all source files in sight (e.g. ``.py``, ``.cpp``), but not any compiled files.
    The ``make build_sdist`` target doesn't need to compile anything.

  - A key point in the above design: the Makefile doesn't need to be aware of the python 
    packaging system (aside from defining targets ``build_wheel``, ``build_sdist``, and 
    writing files ``wheel_files.txt``, ``sdist_files.txt``).

  - In your ``pyproject.toml``, specify ``pipmake`` as ``build-backend`` (under ``build-system``)
    and include ``pipmake`` in both  ``requires`` (under ``build-system``) and ``dependencies``.
    A minimal ``pyptoject.toml`` looks like this::

      [project]
      name = "PROJECT_NAME"
      version = "0.0.1"
      requires-python = ">= 3.11"
      dependencies = [ "pipmake" ]

      [build-system]
      build-backend = "pipmake"
      requires = [ "pipmake" ]

After doing the above, the following commands should work:

  - ``pip install [--user] .`` will invoke ``make build_wheel``, then install your python 
    package.

  - ``pip wheel .`` will invoke ``make build_wheel``, then create a ``.whl`` file. (A ``.whl``
    file is a zip file containing all files in ``wheel_files.txt``, plus some required
    metadata files. The metadata files will be created by ``pipmake`` -- the ``Makefile``
    doesn't need to worry about them.)

  - ``pip install [--user] -e .`` will invoke ``make build_wheel``, then configure the
    local source tree to be an "editable install". This means that local edits to python
    source files are immediately importable (without doing another ``pip install``).

    What about local edits to C++ source files? These aren't quite immediately importable,
    since you do need to recompile with ``make build_wheel``, but you don't need to rerun
    ``pip install``. (I usually write the Makefile so that typing ``make`` suffices.)

  - ``pip uninstall PROJECT_NAME`` will undo an (editable or non-editable) install.

  - ``python -m build --sdist`` will invoke ``make build_sdist``, then create an sdist
    file, with a name like ``dist/{PROJECT_NAME}-{VERSION}.tar.gz``.

    Reminder: sdist files can be uploaded to pypi with ``twine upload SDIST_FILENAME``.
    Before doing this, you may want to test your sdist with ``pip install SDIST_FILENAME``.

Notes:

  - You can freely mix command-line invocations of ``make`` (to build targets in the
    local source tree), and invocations of ``pip`` (to install into python).

  - To conform to python standards, you may want to give python extension modules
    names that end in a suffix like  ``.cpython-313-x86_64-linux-gnu.so``. The
    precise suffix can be obtained by running ``python3-config --extension-suffix`` 
    (this can be done from the Makefile). However, as far as I can tell, this is 
    entirely optional, and nothing bad will happen if you decide to use suffix 
    ``.so`` instead.

  - Linux only for now (should be very easy to support apple/windows, but I haven't
    tried it yet).

We currently impose some heavy-handed constraints on directory layout:
 
  - The project must consist of a single package, rooted here::
    
      ./PROJECT_NAME/__init__.py

  - All installed files (more precisely, all files in ``wheel_files.txt``) must be
    in the ``PROJECT_NAME`` directory.

    To satisfy this constraint, I sometimes create symlinks in Makefiles.
    For example, the ``ksgpu`` repo contains header files ``include/ksgpu/*.hpp`` that I 
    want to install with ``pip install``. To do this, the Makefile creates a symlink::

       ksgpu/include -> ../include

    and the ``wheel_files.txt`` that contains filenames such as::

       ksgpu/include/ksgpu/Array.hpp
       ksgpu/include/ksgpu/Barrier.hpp
          ... more files here ...

    Then, ``pip install`` will install these files in locations of the form
    ``.../site-packages/ksgpu/include/ksgpu/*.hpp``.

  - These layout constraints should be straightforward to generalize -- I just haven't
    meeded to do this yet. In the meantime, some "natural" layouts aren't supported, 
    such as rooting the package at ``src/PROJECT_NAME/__init__.py``.
"""

# A python "build backend" defines a three-function API:
#
#    build_wheel()      invoked by 'pip install' and 'pip wheel'
#    build_editable()   invoked by 'pip install -e'
#    build_sdist():     invoked by 'python -m build --sdist'
#
# References:
#
#    https://peps.python.org/pep-0517/
#    https://peps.python.org/pep-0660/
#    https://packaging.python.org/en/latest/specifications/

from .api import build_wheel, build_editable, build_sdist

# The three-function API is implementd by calling methods in a Builder class.
from .Builder import Builder
