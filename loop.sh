#!/bin/bash

while true; do
  python start.py
  if [ ! -f "RESTART" ]; then
    break
  fi
  rm -f "RESTART"
done
