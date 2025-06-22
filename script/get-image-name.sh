#!/bin/bash

PRJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd "${PRJ_DIR}"

DOCKER_IMAGE_NAME="stephC/lumigo"

if [[ "$(uname)" == "Darwin" ]]; then
    # macOS 用 sed 抓版本號，抓類似 VERSION = "1.0.0" 或 '1.0.0'
    VERSION=$(sed -nE 's/^VERSION *= *["'\'']([^"'\'']+)["'\''].*$/\1/p' src/version.py)
else
    # Linux 用 grep 抓版本號
    VERSION=$(grep -Po '^VERSION\s*=\s*["'\''][^"'\'']+["'\'']' src/version.py | grep -Po '["'\''][^"'\'']+["'\'']' | tr -d "\"'")
fi

# 防呆：如果沒抓到版本，給個預設版本號
if [[ -z "$VERSION" ]]; then
    echo "WARNING: Cannot find version in src/version.py, using default 0.0.0"
    VERSION="0.0.0"
fi

LICENSE_MODE="${LICENSE_MODE:-src}"

repo_and_tag="${DOCKER_IMAGE_NAME}:${VERSION}-${LICENSE_MODE}"

echo "${repo_and_tag}"
