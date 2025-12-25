import shutil
from distutils.core import setup
from pathlib import Path

from Cython.Build import cythonize

except_files = {
    'compile_run.py',
    'wsgi.py',
    'worker.py',
    'setup.py',
    'version.py',
    'server.py',
    'run.py',
}
except_folders = {
    'api',
    'config',
    'lib'
}


def build_dir(dir: Path):
    print('------ path [{}] ------'.format(str(dir)))
    py_files = []
    for item in dir.iterdir():
        if item.is_dir() and str(item) not in except_folders:
            build_dir(item)
        elif item.is_file():
            if (
                    item.suffix == '.py'
                    and '__' not in item.name
                    and item.name not in except_files
            ):
                py_files.append(str(item))
    
    if not py_files:
        return
    
    try:
        setup(
            ext_modules=cythonize(py_files, language_level=3),
            script_args=["build_ext", "-b", 'build', "-t", 'build'],
        )
        pass
    except Exception as ex:
        print("error! ", str(ex))
    
    for item in py_files:
        Path(item).unlink()
        Path(item.replace('.py', '.c')).unlink()
    
    for item in Path('build').rglob('*.so'):
        new_name = item.name.split('.', 1)[0] + '.so'
        print(item, dir.joinpath(new_name))
        shutil.move(item, dir.joinpath(new_name))


if __name__ == '__main__':
    build_dir(Path('.'))
    try:
        shutil.rmtree('build')
    except Exception as ex:
        print("error! ", str(ex))
    
    print('compile finished')
