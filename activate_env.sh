#!/bin/bash
# Activation script for aws-devops-strands-agentcore virtual environment

echo "Activating virtual environment..."
source venv/bin/activate

echo "Virtual environment activated!"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo ""
echo "To deactivate, run: deactivate"
