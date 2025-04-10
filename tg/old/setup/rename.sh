#!/bin/bash

while read -r entry; do
  # Extract the two-digit prefix (e.g., "01") before the underscore
  prefix="${entry%%_*}"

  # If a matching folder exists in tofix, rename it
  if [ -d "automated-translation/$prefix" ]; then
    mv "automated-translation/$prefix" "automated-translation/$entry"
  fi
done < model.txt
