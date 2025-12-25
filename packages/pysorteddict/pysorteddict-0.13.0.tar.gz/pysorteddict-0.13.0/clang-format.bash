#! /usr/bin/env bash

shopt -s extglob globstar

cd "${0%/*}"
files=(src/**/*.{cc,hh})
if [ "$1" = check ]
then
    clang-format --verbose --dry-run -Werror ${files[@]}
else
    clang-format --verbose -i ${files[@]}
fi
