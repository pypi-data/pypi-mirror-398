#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile

import functions
from extract_docs import conf, languages, localedir, sphinx_build

from localecmd import start_cli
from localecmd.cli import create_docs

if __name__ == '__main__':
    for lang in languages:
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Folder to dump the files to convert
            folder = os.path.join(tmpdirname, 'source')
            # Folder where converted and translated files
            folder2 = os.path.join(tmpdirname, 'build')

            # Start cli
            cli = start_cli([functions], lang)
            # Dump myst docstrings
            create_docs(folder)
            cli.close()
            # Write conf.py
            with open(os.path.join(folder, 'conf.py'), 'w') as file:
                file.write(conf)
            # Sphinx options
            options = f"-b markdown -D language={lang} -D locale_dirs={localedir}"
            # Place to save helptext files
            endfolder = os.path.join('locale', lang, 'docs')
            # Generate helptext files in markdown with sphinx # No user input
            subprocess.run([*sphinx_build.split(), folder, folder2, *options.split()])  # noqa: S603

            # Generated helptextfiles
            files = ['functions.md', 'builtins.md']
            # Move helptextfiles to correct directory
            for filename in files:
                os.remove(os.path.join(endfolder, filename))
                shutil.move(os.path.join(folder2, filename), endfolder)
            # Empty build folder to have empty dir for next language
            shutil.rmtree(folder2)
