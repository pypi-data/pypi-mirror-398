#!/bin/bash
shopt -s extglob 
sphinx-build -b html docs/source docs/build
git branch -D pages
git switch --orphan pages
rm -r [[ docs/!(build)/* ]]
mv docs/build/* .
git add !(^.)
git commit -n -m "docs: build docs"
git push --set-upstream origin pages --no-verify --force
git switch main
git branch
