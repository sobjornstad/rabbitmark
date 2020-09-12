#!/bin/bash

if [ ! -d "designer" ]; then
    echo "This script must be run from the project's root directory."
    exit
fi

mkdir -p forms

didUpdate=0
for i in designer/*.ui
do
    moduleName=$(basename $i .ui)
    if [ $i -nt forms/$moduleName.py ]; then
        didUpdate=1
        echo "Updating: $moduleName"
        pyuic5 $i -o rabbitmark/forms/$moduleName.py
    fi
done

if [ $didUpdate != 1 ]; then
    echo "No forms to update."
fi

echo "Updating resources..."
pyrcc5 resources/resources.qrc -o rabbitmark/forms/resources_rc.py
# hack because file is generated with wrong import syntax
sed -ie 's/^import resources_rc$/from . import resources_rc/' rabbitmark/forms/about.py
