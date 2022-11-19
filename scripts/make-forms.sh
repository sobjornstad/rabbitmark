#!/usr/bin/env bash

compile_from="designer"
compile_to="rabbitmark/gui/forms"
qrc_file="resources/resources.qrc"
qrc_compiled="$compile_to/resources_rc.py"


if [ ! -d "$compile_from" ]; then
    echo "This script must be run from the project's root directory."
    exit 1
fi

mkdir -p "$compile_to"

echo "Updating forms..."
didUpdate=0
for i in "$compile_from"/*.ui; do
    moduleName="$(basename "$i" .ui)"
    if [ "$i" -nt "$compile_to/$moduleName.py" ]; then
        didUpdate=1
        echo "  Updating: $moduleName"
        pyuic5 "$i" -o "$compile_to/$moduleName.py"
    fi
done
touch "$compile_to/__init__.py"

if [ $didUpdate -ne 1 ]; then
    echo "  No forms to update."
fi

echo "Updating resources..."
if [ "$qrc_file" -nt "$qrc_compiled" ]; then
    pyrcc5 "$qrc_file" -o "$qrc_compiled"
    # Hack because pyrcc generates the file using an invalid import syntax.
    for i in "$compile_to"/*.py; do
        sed -i -e 's/^import resources_rc$/from . import resources_rc/' "$i"
    done
    echo "  done."
else
    echo "  No resources to update."
fi
