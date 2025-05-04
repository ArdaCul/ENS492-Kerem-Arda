#!/bin/bash

VENV_DIR="venv"

# Detect OS and set activation script
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32"* ]]; then
    ACTIVATE_SCRIPT="$VENV_DIR/Scripts/activate"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Step 1: Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR" || python -m venv "$VENV_DIR"
    echo "Virtual environment created at '$VENV_DIR'"
else
    echo "Virtual environment found. Skipping creation."
fi

# Step 2: Activate venv
echo "Activating virtual environment..."
source "$ACTIVATE_SCRIPT"

# Step 3: Install requirements if venv was just created
REQ_FILE=".venv_initialized"
if [ ! -f "$REQ_FILE" ]; then
    echo "Installing required packages..."
    pip install --upgrade pip
    pip install \
    aiohappyeyeballs==2.6.1 \
    aiohttp==3.11.18 \
    aiosignal==1.3.2 \
    anyio==4.9.0 \
    asyncclick==8.1.8.0 \
    attrs==25.3.0 \
    blinker==1.9.0 \
    certifi==2025.1.31 \
    cffi==1.17.1 \
    charset-normalizer==3.4.1 \
    click==8.1.8 \
    cryptography==44.0.2 \
    Flask==3.1.0 \
    frozenlist==1.6.0 \
    idna==3.10 \
    itsdangerous==2.2.0 \
    Jinja2==3.1.6 \
    MarkupSafe==3.0.2 \
    mashumaro==3.15 \
    multidict==6.4.3 \
    propcache==0.3.1 \
    pycparser==2.22 \
    pycryptodome==3.22.0 \
    pytapo==2.0 \
    python-kasa==0.10.2 \
    requests==2.32.3 \
    rtp==0.0.4 \
    sniffio==1.3.1 \
    typing_extensions==4.13.2 \
    urllib3==2.4.0 \
    Werkzeug==3.1.3 \
    yarl==1.20.0

    touch "$REQ_FILE"
    echo "Dependencies installed."
else
    echo "Dependencies already installed. Skipping."
fi

# Step 4: Run the Flask app
echo "Running app.py..."
python app.py
