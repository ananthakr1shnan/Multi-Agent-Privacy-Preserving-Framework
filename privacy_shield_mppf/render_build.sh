#!/bin/bash
# Render.com deployment script

echo "Starting MPPF deployment..."

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

echo "Deployment setup complete!"
