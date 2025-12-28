import os
import re
import io
import sys
import tomllib
import zipfile
import tarfile
import editables
import subprocess


class Builder:
    def __init__(self, outdir):
        """The Builder class provides methods which are used to implement the three-function "build backend" API.

        The constructor reads the pyproject.toml file, and initializes the members::

             self.name
             self.version
             self.requires_python  # e.g. '>= 3.8'
             self.dependencies     # list of strings, e.g. ['numpy','scipy']
             self.wheel_tag        # 'py3-none-any'
             self.wheel_basename   # '{name}-{version}-{tag}.whl'
             self.wheel_filename   # '{outdir}/{wheel_basename}'
             self.sdist_basename   # '{name}-{version}.tar.gz'
             self.sdist_filename   # '{outdir}/{sdist_basename}'
             self.outdir           # constructor argument

        Currently, we just parse the 'name' and 'version' fields, in order to generate filenames
        such as ``{name}-{version}.dist-info``. I might add more fields later.

        Reference: https://packaging.python.org/en/latest/specifications/pyproject-toml/
        """
        
        filename = 'pyproject.toml'
        print(f'pipmake: reading {filename}')

        if not os.path.exists(filename):
            raise RuntimeError(f'{filename} not found')
        
        with open(filename, 'rb') as f:
            data = tomllib.load(f)

        fields = [ 'name', 'version', 'requires-python', 'dependencies' ]
        
        if 'project' not in data:
            raise RuntimeError(f"{filename}: expected [project] header")
        for f in fields:
            if f not in data['project']:
                raise RuntimeError(f"{filename}: expected [project] header to have '{f}' field")

        self.name = data['project']['name']
        self.version = data['project']['version']
        self.requires_python = data['project']['requires-python']
        self.dependencies = data['project']['dependencies']
        self.scripts = data['project'].get('scripts', {})
        print(f'pipmake: name={self.name}, version={self.version}')
        # print(f'pipmake: requires_python = "{self.requires_python}"')
        # print(f'pipmake: dependencies = {self.dependencies}')

        # We don't "normalize" the name -- this just causes problems.
        # (Ref: https://packaging.python.org/en/latest/specifications/name-normalization/#name-normalization)
        
        if not self.is_valid_name(self.name):
            raise RuntimeError(f"{filename}: name = '{self.name}' is invalid")
        if not self.is_valid_version(self.version):
            raise RuntimeError(f"{filename}: version = '{self.version}' is invalid")
        # FIXME how to validate self.requires_python?

        # FIXME I haven't figured out tags yet.
        # Reference: https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
        
        self.wheel_tag = 'py3-none-any'
        self.wheel_basename = f'{self.name}-{self.version}-{self.wheel_tag}.whl'
        self.wheel_filename = os.path.join(outdir, self.wheel_basename)
        self.sdist_basename = f'{self.name}-{self.version}.tar.gz'
        self.sdist_filename = os.path.join(outdir, self.sdist_basename)
        self.outdir = outdir


    def invoke_makefile(self, makefile_target):
        """Runs ``make {makefile_target}`` in a subprocess, and throws an exception if anything goes wrong."""
        
        self.makefile_target = makefile_target

        if subprocess.run(['which','make']).returncode:
            raise RuntimeError("pipmake: fatal: the 'make' command-line utility is not installed (or is not in $PATH)")
        
        args = ['make', f'-j{os.cpu_count()}', makefile_target]
        make_cmdline = ' '.join(args)
        
        print(f"pipmake: invoking '{make_cmdline}'")
        sys.stdout.flush()

        if subprocess.run(args).returncode:
            raise RuntimeError(f"pipmake: fatal: '{make_cmdline}' failed")
        

    def read_file_list(self, list_filename, enforce_package_dir=True):
        """Reads a text file containing one filename per line, and stores the result in ``self.filename_list``.
        
        Used to read ``wheel_files.txt`` and ``sdist_files.txt`` (created by ``make build_wheel`` and ``make build_sdist``).

        Throws an exception if a file doesn't exist. 

        If ``enforce_package_dir=True``, then an exception is thrown if a filename is outside the toplevel package dir.
        (We set this to True for ``wheel_files.txt`` and false for ``sdist_files.txt``.)"""
    
        print(f"pipmake: reading {list_filename}")
    
        if not os.path.exists(list_filename):
            raise RuntimeError(f"{list_filename} does not exist (should have been created in 'make {self.makefile_target}')")

        self.list_filename = list_filename
        self.filename_list = [ ]

        with open(list_filename) as f:
            for line in f:
                # Remove comment, if any
                ix = line.find('#')
                if ix >= 0:
                    line = line[:ix]
            
                # Note: split() also strips leading/trailing whitespace
                s = line.split()
            
                if len(s) == 0:
                    continue
                if len(s) != 1:
                    # We treat lines containing whitespace as an error (even though in principle, filenames can contain whitespace).
                    raise RuntimeError(f"{list_filename}: line '{line}' contains whitespace; this is currently treated as an error")

                self.filename_list.append(s[0])

        dl_msg = f'See "heavy-handed constraints on directory layout" here: https://pipmake.readthedocs.io/en/latest/usage.html'

        if f'{self.name}/__init__.py' not in self.filename_list:
            raise RuntimeError(f"{list_filename}: expected filename '{self.name}/__init__.py' to appear. {dl_msg}")

        for filename in self.filename_list:
            if enforce_package_dir and not filename.startswith(f'{self.name}/'):
                raise RuntimeError(f"{list_filename}: expected all filenames to begin with '{self.name}/' (got filename='{filename}'). {dl_msg}")
            if not os.path.exists(filename):
                raise RuntimeError(f"{list_filename}: filename='{filename}' not found in filesystem")


    def write_wheel(self, editable):
        """Writes a wheel file to disk. Called by ``build_wheel()`` and ``build_editable()``.

        Reference: https://packaging.python.org/en/latest/specifications/binary-distribution-format/#file-contents"""

        print(f'pipmake: writing wheel {self.wheel_filename}')

        dist_info_dir = f'{self.name}-{self.version}.dist-info'
        
        with zipfile.ZipFile(self.wheel_filename, 'x') as wheel:
            if not editable:
                # Case 1: non-editable wheel.
                # We add files from 'wheel_files.txt'.
                primary_filenames = self.filename_list
                primary_label = f'from {self.list_filename}'
                for filename in primary_filenames:
                    wheel.write(filename)
                
            else:
                # Case 2: editable wheel.
                # We use the 'editables' library to create the .pth and .py files.
                e = editables.EditableProject(self.name, os.getcwd())
                e.map(self.name, self.name)

                primary_filenames = [ ]
                for filename, contents in e.files():
                    wheel.writestr(filename, contents)
                    primary_filenames.append(filename)
                    
                primary_label = ', '.join(primary_filenames)
                
            print(f"pipmake: added {len(primary_filenames)} files to wheel ({primary_label})")

            # Remaining code adds metadata files.
            metadata = {
                f'{dist_info_dir}/METADATA': self._make_metadata(),
                f'{dist_info_dir}/WHEEL': self._make_wheel_wheel(),
                f'{dist_info_dir}/top_level.txt': (self.name + '\n')  # not sure if I need this
            }

            # Add entry_points.txt if there are console scripts defined in [project.scripts]
            entry_points = self._make_entry_points()
            if entry_points:
                metadata[f'{dist_info_dir}/entry_points.txt'] = entry_points
            
            record_filename = f'{dist_info_dir}/RECORD'
            all_filenames = primary_filenames + list(metadata.keys()) + [record_filename]
            metadata[record_filename] = self._make_wheel_record(all_filenames)
            
            print(f"pipmake: adding {len(metadata)} metadata files to wheel")
            
            for filename, contents in metadata.items():
                wheel.writestr(filename, contents)

        print(f'pipmake: {self.wheel_filename} written successfully')


    def write_sdist(self):
        """Writes an sdist file to disk."""
        
        topdir = f'{self.name}-{self.version}'
        print(f'pipmake: writing sdist {self.sdist_filename}, {topdir=}')
        
        with tarfile.open(self.sdist_filename, 'w:gz') as sdist:
            print(f"pipmake: adding {len(self.filename_list)} files to sdist (from {self.list_filename})")
            
            for filename in self.filename_list:
                sdist.add(filename, f'{topdir}/{filename}')

            metadata = { f'{topdir}/PKG-INFO': self._make_metadata() }
            print(f"pipmake: adding {len(metadata)} metadata file(s) to sdist")
            
            for filename, contents in metadata.items():
                # Adding a string to a tarfile is awkward.
                # Reference: https://stackoverflow.com/questions/13988973/how-does-one-add-string-to-tarfile-in-python3
                tarinfo = tarfile.TarInfo(name = filename)
                tarinfo.size = len(contents)
                sdist.addfile(tarinfo, io.BytesIO(contents.encode('utf8')))
        
        print(f'pipmake: {self.sdist_filename} written successfully')

    
    def _make_metadata(self):
        """Returns a "core metadata" object, used in both sdists and wheels.

        In an sdist, it has a filename like '{name}-{version}/PKG-INFO'.
        In a wheel, it has a filename like '{name}-{version}.dist-info/METADATA'.

        Reference: https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata.
        """

        with io.StringIO() as s:
            print(f'Metadata-Version: 2.2', file=s)
            print(f'Name: {self.name}', file=s)
            print(f'Version: {self.version}', file=s)
            print(f'Requires-Python: {self.requires_python}', file=s)

            for d in self.dependencies:
                print(f'Requires-Dist: {d}', file=s)
            
            return s.getvalue()


    def _make_wheel_wheel(self):
        """Returns contents of file '{name}-{version}.dist-info/WHEEL', which is part of the .whl format."""

        # FIXME the docs (https://packaging.python.org/en/latest/specifications/binary-distribution-format/#file-contents)
        # say that this file is required, but I couldn't find a spec for it. I just unpacked a .whl file created by
        # setuptools, and inspected the file.

        with io.StringIO() as s:
            print(f'Wheel-Version: 1.0', file=s)
            print(f'Generator: pipmake (0.0.1)', file=s)   # FIXME getting version from within pipmake?
            print(f'Root-Is-Purelib: true', file=s)        # FIXME what is this?
            print(f'Tag: {self.wheel_tag}', file=s)
            return s.getvalue()


    def _make_wheel_record(self, wheel_output_files):
        """Returns contents of file '{name}-{version}.dist-info/RECORD', which is part of the .whl format."""

        # FIXME the docs (https://packaging.python.org/en/latest/specifications/binary-distribution-format/#signed-wheel-files)
        # say that the RECORD file must include cryptographic hashes, but empirically it seems to work fine if these are omitted.

        with io.StringIO() as s:
            for f in wheel_output_files:
                print(f'{f},,', file=s)
            return s.getvalue()


    def _make_entry_points(self):
        """Returns contents of '{name}-{version}.dist-info/entry_points.txt' for console scripts.
        
        Pip reads this file during installation and generates wrapper scripts in the bin directory.
        Reference: https://packaging.python.org/en/latest/specifications/entry-points/
        """
        
        if not self.scripts:
            return None
        
        with io.StringIO() as s:
            print('[console_scripts]', file=s)
            for name, entry_point in self.scripts.items():
                print(f'{name} = {entry_point}', file=s)
            return s.getvalue()

        
    @staticmethod    
    def is_valid_name(name):
        """Reference: https://packaging.python.org/en/latest/specifications/name-normalization/#name-format"""
        return re.match(r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", name, re.IGNORECASE) is not None

    @staticmethod
    def is_valid_version(version):
        """Reference: https://packaging.python.org/en/latest/specifications/version-specifiers/#appendix-parsing-version-strings-with-regular-expressions"""
        s = r'^([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$'
        return re.match(s, version) is not None
