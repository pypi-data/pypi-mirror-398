#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile

sphinx_build = sys.executable + ' -m sphinx.cmd.build'
sphinx_intl = sys.executable + ' -m sphinx_intl'
# Languages to translate helptexts to
languages = ['en_GB', 'de_DE']

home_dir = os.path.split(__file__)[0]
localedir = os.path.join(home_dir, 'locale')
# Content of conf.py file
# myst extensions are used in the builtins docstrings and enable use of myst in parameter
# descriptions.
conf = """
extensions = [
    'localecmddoc',
    'myst_parser',
    'sphinx_markdown_builder',
]
localecmd_modules = {
    'functions': 'functions',
    }


myst_enable_extensions = [
    "fieldlist",
    "colon_fence",
]

source_suffix = {'.md': 'markdown'}
gettext_compact = True
"""
if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Folder to dump the  raw docstrings
        folder = os.path.join(tmpdirname, 'source')
        # Folder where converted and translated files
        folder2 = os.path.join(tmpdirname, 'build')

        # Write conf.py
        with open(os.path.join(folder, 'conf.py'), 'w') as file:
            file.write(conf)

        # Sphinx options
        options = "-b gettext"
        # Extract translatable strings # No user input
        subprocess.run([*sphinx_build.split(), folder, folder2, *options.split()])  # noqa: S603

        options = f"update -p {folder2} -d locale"
        # Languages to update: -l en_GB -l de_DE
        # lang_str = ' '.join([f'-l {lang}' for lang in languages])
        # Update .po files
        subprocess.run([*sphinx_intl.split(), *options.split()])  # noqa: S603
