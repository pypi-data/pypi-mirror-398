#!/bin/bash


# temporary rename pyproject.toml
mv pyproject.toml pyproject.toml.bak

# Install from requirements.txt
pip install -r requirements.txt

# Rename back
mv pyproject.toml.bak pyproject.toml

