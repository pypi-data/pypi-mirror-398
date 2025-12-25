#!/bin/bash

set -e

# Accept new parameters
env_build_path=$1
squashfs_file_path=$2
yaml_file_path=$3
py_version=$4

# Validate inputs
if [ -z "$yaml_file_path" ] || [ -z "$squashfs_file_path" ] || [ -z "$env_build_path" ] || [ -z "$py_version" ]; then
    echo "Error: Missing required parameters"
    exit 1
fi

if [ ! -f "$yaml_file_path" ]; then
    echo "Error: YAML file does not exist: $yaml_file_path"
    exit 1
fi

# Set unique cache dir per environment

squashfs_file_name="$(basename "${squashfs_file_path}")"
env_name_with_version="${squashfs_file_name%.squashfs}"
export CONDA_PKGS_DIRS="/dataflow/env/cache/${env_name_with_version}/"

mkdir -p "$CONDA_PKGS_DIRS"
conda config --set always_copy true

export PIP_CONSTRAINT="/dataflow/setup/pip_constraints/py${py_version}-constraints.txt"
export NO_CONDA_PLUGIN_PIP_CONSTRAINT="true"

# Create the conda environment from the YAML file with pip no-cache
conda env create --file "$yaml_file_path" --prefix "${env_build_path}" --yes
conda env export --prefix "${env_build_path}" > "$yaml_file_path"

# Create squashfs file
mksquashfs "${env_build_path}" "${squashfs_file_name}" -comp zstd -Xcompression-level 4
cp -f "${squashfs_file_name}" "${squashfs_file_path}"

echo "Environment Creation Successful"