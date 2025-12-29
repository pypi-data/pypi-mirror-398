import base64
import hashlib
import io
import pathlib
import tarfile
import tomllib
import zipfile

# TODO: Look for .gitignore for excludes
# TODO: Look for pyproject.toml includes/excludes


EDITABLE_FINDER = """
import importlib.abc

class EditableFinder(importlib.abc.MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if fullname == '{name}':
            import os, importlib
            locations = [os.path.dirname('{path}')]
            return importlib.util.spec_from_file_location(
                fullname, '{path}', submodule_search_locations=locations)
        return None

sys.meta_path.insert(0, EditableFinder())
"""


def build_sdist(sdist_directory, config_settings=None):
    src, name, version, pyproject = project_info()
    outdir = pathlib.Path(sdist_directory).resolve()
    outfile = outdir / f'{name}-{version}.tar.gz'
    root = f'{name}-{version}'

    with tarfile.open(outfile, 'w:gz') as f:
        for path in src.rglob('*'):
            if path.is_dir():
                continue
            relative = path.relative_to(src)
            if _should_exclude(relative):
                continue
            f.add(path, f'{root}/{relative}')
        metadata = _format_key_value([
            ('Metadata-Version', '2.1'),
            ('Name', name),
            ('Version', version),
        ])
        info = tarfile.TarInfo(f'{root}/PKG-INFO')
        info.size = len(metadata)
        f.addfile(info, io.BytesIO(metadata))

    return outfile.name


def build_wheel(
    wheel_directory, config_settings=None, metadata_directory=None,
):
    src, name, version, pyproject = project_info()
    deps = pyproject['project'].get('dependencies', [])

    with Wheel(wheel_directory, name, version, deps) as wheel:
        for path in src.rglob('*.py'):
            relative = path.relative_to(src)
            if _should_exclude(relative):
                continue
            wheel.add(f'{name}/{relative}', path.read_bytes())
    return wheel.filename


def build_editable(
    wheel_directory, config_settings=None, metadata_directory=None,
):
    src, name, version, pyproject = project_info()
    deps = pyproject['project'].get('dependencies', [])

    path = str(src / '__init__.py').as_posix()
    finder = repr(EDITABLE_FINDER.format(name=name, path=path))
    # finder = 'import sys; exec("""' + finder + '""")'
    finder = f'import sys; exec({finder})'
    finder = finder.encode('utf-8')
    with Wheel(wheel_directory, name, version, deps) as wheel:
        wheel.add(f'_editable_impl_{name}.pth', finder)
    return wheel.filename


def project_info():
    src = pathlib.Path('.').resolve()
    assert (src / '__init__.py').exists()
    pyproject = tomllib.loads((src / 'pyproject.toml').read_text())
    name = pyproject['project'].get('name', src.name)
    version = pyproject['project'].get('version', '0.0.0')
    return src, name, version, pyproject


class Wheel:

    def __init__(self, outdir, name, version, deps):
        outdir = pathlib.Path(outdir).resolve()
        self.name = name
        self.version = version
        self.deps = deps or []
        self.path = outdir / f'{name}-{version}-py3-none-any.whl'
        self.records = []
        self.f = None

    @property
    def filename(self):
        return self.path.name

    def __enter__(self):
        assert not self.f
        self.f = zipfile.ZipFile(self.path, 'w')
        self.f.__enter__()
        return self

    def __exit__(self, typ, val, tb):
        self._finish()
        self.records = []
        self.f.__exit__(typ, val, tb)
        self.f = None

    def add(self, name, content):
        assert isinstance(content, bytes), (name, content)
        name = str(name)
        digest = _get_digest(content)
        self.records.append(f'{name},{digest},{len(content)}\n')
        self.f.writestr(name, content)

    def _finish(self):
        distinfo = f'{self.name}-{self.version}.dist-info'
        self.add(f'{distinfo}/METADATA', _format_key_value([
            ('Metadata-Version', '2.1'),
            ('Name', self.name),
            ('Version', self.version),
            *[('Requires-Dist', x) for x in self.deps],
        ]))
        self.add(f'{distinfo}/WHEEL', _format_key_value([
            ('Wheel-Version', '1.0'),
            ('Generator', 'tinybuild 0.1.0'),
            ('Root-Is-Purelib', 'true'),
            ('Tag', 'py3-none-any'),
        ]))
        self.records.append('RECORD,,\n')
        self.f.writestr(f'{distinfo}/RECORD', ''.join(self.records))


def _should_exclude(path):
    parts = path.parts
    return (
        path.suffix == '.pyc' or
        any(part.startswith('.') for part in parts) or
        'dist' in parts or
        'build' in parts or
        '__pycache__' in parts
    )


def _get_digest(data):
    digest = hashlib.sha256(data).digest()
    digest = base64.urlsafe_b64encode(digest)
    digest = 'sha256=' + digest.decode('latin1').rstrip('=')
    return digest


def _format_key_value(data):
    content = ''.join(f'{k}: {v}\n' for k, v in data)
    content = content.encode('utf-8')
    return content
