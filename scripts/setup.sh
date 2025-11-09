#!/bin/bash
# Setup script for ELAOMS

echo "Setting up Eleven Labs Agents Open Memory System (ELAOMS)..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cat > .env << EOF
# OpenMemory Configuration
OPENMEMORY_URL=http://localhost:8080
OPENMEMORY_API_KEY=your_openmemory_api_key_here

# Eleven Labs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_WEBHOOK_SECRET=your_webhook_secret_here

# ngrok Configuration (optional, for local development)
NGROK_AUTH_TOKEN=your_ngrok_auth_token_here
EOF
    echo ".env file created. Please update it with your actual credentials."
else
    echo ".env file already exists."
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete!"
echo "Please update .env with your actual credentials before running the service."

