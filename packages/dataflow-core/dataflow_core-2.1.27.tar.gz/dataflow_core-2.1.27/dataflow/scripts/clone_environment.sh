#!/bin/bash
set -e

source_env_path=$1
env_build_path=$2
squashfs_file_path=$3
yaml_file_path=$4

# Set unique cache dir per environment
export PIP_NO_CACHE_DIR=1

# 1. Cloning conda env to temporary location

squashfs_file_name="$(basename "${squashfs_file_path}")"
env_name_with_version="${squashfs_file_name%.squashfs}"

export CONDA_PKGS_DIRS="/dataflow/env/cache/${env_name_with_version}/"

mkdir -p "$CONDA_PKGS_DIRS"
conda config --set always_copy true

conda create --clone ${source_env_path} --prefix ${env_build_path} --yes
conda env export --prefix "${env_build_path}" > "$yaml_file_path"

# 2. Create squashfs file from the cloned environment
mksquashfs "${env_build_path}" "${squashfs_file_name}" -comp zstd -Xcompression-level 4
cp -f "${squashfs_file_name}" "${squashfs_file_path}"
# 3. Cleanup the temporary environment directory
rm -rf "${env_build_path}"
rm -f "${squashfs_file_name}"
rm -rf "$CONDA_PKGS_DIRS"

echo "Environment Creation Successful"