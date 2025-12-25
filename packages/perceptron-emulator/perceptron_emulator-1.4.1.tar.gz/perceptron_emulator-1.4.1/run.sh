#!/bin/bash
# Simple script to run the perceptron emulator locally

cd "$(dirname "$0")"
source venv/bin/activate
python -m perceptron_emulator.main
