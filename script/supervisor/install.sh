#!/usr/bin/env bash

platform='unknown'
unamestr=`uname`
if [[ "$unamestr" == 'Linux' ]]; then
    platform='linux'
fi

if [[ $platform == 'linux' ]]; then

    SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    TARGET_DIR="/etc/supervisor/conf.d"

    for FILE in `find $SOURCE_DIR -name "*.conf"`;
    do
        echo "Creating symbolc links for "$(basename $FILE);
        test -e $TARGET_DIR/$(basename $FILE) || ln -s $FILE $TARGET_DIR
    done

    service supervisor restart;
fi
