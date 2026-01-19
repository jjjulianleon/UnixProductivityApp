#!/bin/bash
# Package the plasmoid
cd plasmoid/package
zip -r ../../unix-productivity-widget.plasmoid .
echo "Created unix-productivity-widget.plasmoid"
