#!/bin/bash

rm -rf build dist *.egg-info

python3 setup.py bdist_wheel --universal


rm -rf build *.egg-info



