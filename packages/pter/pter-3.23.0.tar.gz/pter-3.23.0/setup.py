#!/usr/bin/env python3
import sys
from pathlib import Path

import setuptools
from setuptools.command.build_py import build_py
from setuptools.command.install import install


try:
    import docutils.core
    from docutils.writers import manpage
except ImportError:
    docutils = None
    manpage = None


def compile_documentation():
    if docutils is None or manpage is None:
        return

    dst = Path('pter/docs')
    dst.mkdir(exist_ok=True)
    docpath = Path('doc')
    
    Path('man').mkdir(exist_ok=True)

    for fn in ['pter.rst', 'qpter.rst', 'pter.config.rst']:
        fn = docpath / fn
        if not fn.is_file():
            continue
        dstfn = str(dst / (fn.stem + '.html'))
        docutils.core.publish_file(source_path=str(fn),
                                   destination_path=dstfn,
                                   writer_name='html')

        if fn.stem == 'pter.config':
            docutils.core.publish_file(source_path=str(fn),
                                       destination_path='man/pter.config.5',
                                       writer_name='manpage')
        elif fn.stem in ['pter', 'qpter']:
            docutils.core.publish_file(source_path=str(fn),
                                       destination_path='man/' + fn.stem + '.1',
                                       writer_name='manpage')


def select_manpages():
    src = Path('man')
    paths = []
    if not src.is_dir():
        compile_documentation()
    if not src.is_dir():
        return paths
    for item in src.iterdir():
        section = item.name
        if '.' not in section:
            continue
        section = section.split('.')[-1]
        if section not in ['1', '5']:
            continue
        paths.append((f'share/man/man{section}/', [str(item)]))

    return paths


class BuildDocs(build_py):
    def run(self):
        super().run()
        compile_documentation()


if __name__ == '__main__':
    setuptools.setup(cmdclass={"build_py": BuildDocs,},
                     data_files=select_manpages())
