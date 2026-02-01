#!/bin/bash
# Package the plasmoid
cd plasmoid/package
zip -r ../../unidex-widget.plasmoid .
echo "Created unidex-widget.plasmoid"
