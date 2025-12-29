#! /usr/bin/env bash

function bluer_ai_pypi_install() {
    pip3 install --upgrade setuptools wheel twine
    python3 -m pip install --upgrade build
}
