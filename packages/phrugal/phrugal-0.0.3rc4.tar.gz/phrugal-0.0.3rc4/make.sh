#!/bin/sh

# Change to the directory of the script
cd "$(dirname "$0")"

# Command file for Sphinx documentation

if [ -z "$SPHINXBUILD" ]; then
    SPHINXBUILD=sphinx-build
fi
SOURCEDIR=doc
BUILDDIR=doc/_build

# Check if sphinx-build is available
if ! command -v $SPHINXBUILD >/dev/null 2>&1; then
    echo
    echo "The 'sphinx-build' command was not found. Make sure you have Sphinx"
    echo "installed, then set the SPHINXBUILD environment variable to point"
    echo "to the full path of the 'sphinx-build' executable. Alternatively you"
    echo "may add the Sphinx directory to PATH."
    echo
    echo "If you don't have Sphinx installed, grab it from"
    echo "https://www.sphinx-doc.org/"
    exit 1
fi

if [ $# -eq 0 ]; then
    $SPHINXBUILD -M help "$SOURCEDIR" "$BUILDDIR" $SPHINXOPTS $O
else
    $SPHINXBUILD -M $1 "$SOURCEDIR" "$BUILDDIR" $SPHINXOPTS $O
fi
