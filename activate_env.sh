#!/bin/bash
# Activation script for aws-devops-strands-agentcore virtual environment
# Activate: $ sudo chmod -R 755  ./venv/bin; source venv/bin/activate 
# Deactivate: $ deactivate

echo "Activating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Virtual environment activated!"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo ""
echo "To deactivate, run: deactivate"
