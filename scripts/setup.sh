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
ELEVENLABS_POST_CALL_HMAC_KEY=your_post_call_hmac_key_here
ELEVENLABS_CLIENT_DATA_WORKSPACE_SECRET=your_client_data_workspace_secret_here

# Webhook Storage Configuration
WEBHOOK_STORAGE_PATH=data/webhooks
WEBHOOK_QUARANTINE_PATH=data/webhooks/quarantine
AUDIO_CACHE_TTL=3600
WEBHOOK_RETENTION_DAYS=30
MAX_RETRIES=3
ANOMALY_DETECTION_ENABLED=true
ANOMALY_FAILURE_THRESHOLD=5
ANOMALY_WINDOW_SECONDS=300
ALERT_ON_QUARANTINE_FAILURES=true
REDIS_URL=
REDIS_TTL=3600
FILE_PERMISSIONS_MODE=384
ENABLE_ENCRYPTION_AT_REST=false
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

