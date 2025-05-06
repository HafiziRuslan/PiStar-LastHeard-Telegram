#!/bin/bash
set -e
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi
echo "Activating virtual environment"
source venv/bin/activate
echo "Installing dependencies"
pip install -r requirements.txt
echo "Running main.py"
python3 ./main.py

