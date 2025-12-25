#!/bin/bash
#
# setup.sh - Download and build adaptagrams dependency
#
set -e  # Exit on error

CWD="$(pwd)"
NAME="adaptagrams"
THIRDPARTY="${CWD}/thirdparty"
PREFIX="${THIRDPARTY}/${NAME}"

get_adaptagrams() {
    echo "Fetching ${NAME} from fork..."
    mkdir -p build "${THIRDPARTY}"
    cd build
    if [ ! -d "${NAME}" ]; then
        git clone --depth 1 https://github.com/shakfu/adaptagrams.git
    fi
    cd "${NAME}"
    make install
    mv build/install "${PREFIX}"
}

remove_current() {
    echo "Removing existing build artifacts..."
    rm -rf build thirdparty
}

main() {
    remove_current
    get_adaptagrams
    echo "Done. Adaptagrams installed to ${PREFIX}"
}

main
