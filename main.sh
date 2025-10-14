#!/bin/bash
set -e
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one."
    python3 -m venv venv
    echo "Installing dependencies"
    pip install -r requirements.txt
else
    echo "Virtual environment already exists."
fi
echo "Activating virtual environment"
source venv/bin/activate
echo "Running main.py"
while true; do
    python3 ./main.py
    echo "Script exited. Waiting for 10 seconds before the next run."
    sleep 10
done
