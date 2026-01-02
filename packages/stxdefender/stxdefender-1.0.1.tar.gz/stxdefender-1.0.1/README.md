# STXDefender - Python Source Code Encryption Tool

**STXDefender** provides enterprise-grade protection for your Python source code using AES-256-GCM encryption. Safeguard your intellectual property with military-grade cryptography, license management, and flexible access control.

## Features

- 🔒 **AES-256-GCM Encryption** - Industry-standard authenticated encryption
- 🔑 **License Activation** - Secure token-based activation system with online validation
- ⏱️ **Enforced Expiry (TTL)** - Control access with customizable expiration times
- 🔐 **Custom Password Support** - Use your own passwords or auto-generated secure keys
- 🆓 **Trial Mode** - Test the tool with 24-hour encrypted file limits
- 🚀 **Direct Execution** - Run encrypted `.pye` files directly with Python
- 💻 **Simple CLI** - Intuitive commands: `activate`, `validate`, `encrypt`
- 📊 **Web Dashboard** - Manage licenses, tokens, and subscriptions through a modern web interface

## Installation

### Install from PyPI (Recommended)

```bash
pip install stxdefender
```

After installation, the `stxdefender` command will be available globally.

### Install from Source

If you want to install from the source code:

```bash
# Navigate to project directory
cd "path/to/sourcedefender remake"

# Install in editable mode
pip install -e .
```

### Quick Setup (Windows)

**Automated setup with server:**

1. Double-click `setup_and_run.bat`
   - Installs all dependencies
   - Sets up the CLI tool
   - Starts the backend server

2. Or use `START.bat` for a quick start (assumes dependencies are installed)

3. Or use `INSTALL.bat` to just install dependencies without starting

### Quick Setup (Linux/Mac)

```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

## Quick Start Guide

### 1. Start the Backend Server

If you installed from source and want to run your own server:

```bash
cd backend
python app.py
```

The server will start on `http://localhost:5000`

### 2. Create an Account

1. Open your browser and go to `http://localhost:5000`
2. Click "Sign up" and create an account
3. Log in to access the dashboard

### 3. Generate an Activation Token

1. In the dashboard, click "Generate New Token"
2. Copy the token (you'll only see it once!)

### 4. Activate STXDefender

```bash
stxdefender activate --token YOUR_TOKEN_HERE
```

### 5. Validate Activation

```bash
stxdefender validate
```

### 6. Encrypt Your Python Files

```bash
# Basic encryption
stxdefender encrypt myapp.py

# With expiration (24 hours)
stxdefender encrypt --ttl=24h myapp.py

# With custom password
stxdefender encrypt --password=mysupersecret myapp.py

# Remove original file after encryption
stxdefender encrypt --remove myapp.py
```

This creates an encrypted `.pye` file (e.g., `myapp.pye`).

### 7. Run Encrypted Files

```bash
# Run encrypted file directly
python myapp.pye

# With custom password (if used during encryption)
export STXDEFENDER_PASSWORD="mysupersecret"
python myapp.pye

# On Unix/Linux/Mac, make executable and run directly
chmod +x myapp.pye
./myapp.pye
```

## Command Reference

### `stxdefender activate --token <token>`

Activate your license with a token obtained from the dashboard.

```bash
stxdefender activate --token 470a7f2e76ac11eb94390242ac130002
```

### `stxdefender validate`

Check your current license activation status.

```bash
stxdefender validate
```

### `stxdefender encrypt [options] <file>`

Encrypt a Python source file.

**Options:**
- `--remove` - Remove the original file after encryption
- `--ttl=<time>` - Set expiration time (e.g., `24h`, `7d`, `30m`, `1w`)
- `--password=<pass>` - Use a custom password (otherwise auto-generated)

**Examples:**

```bash
# Basic encryption
stxdefender encrypt script.py

# With 24-hour expiration and remove original
stxdefender encrypt --remove --ttl=24h myapp.py

# With custom password
stxdefender encrypt --password=mysecret script.py

# Complex example
stxdefender encrypt --remove --ttl=7d --password=supersecret myapp.py
```

## TTL (Time To Live) Format

The `--ttl` option accepts the following formats:

- `30s` - 30 seconds
- `5m` - 5 minutes
- `24h` - 24 hours
- `7d` - 7 days
- `2w` - 2 weeks
- `365` - 365 seconds (numeric only = seconds)

## Password Handling

### Auto-generated Password

If no password is specified, STXDefender generates a secure random password. This password is embedded in the encrypted file, making the file self-contained and ready to run.

### Custom Password

You can specify a custom password during encryption:

```bash
stxdefender encrypt --password=mypassword script.py
```

When running the encrypted file, set the password as an environment variable:

```bash
# Unix/Linux/Mac
export STXDEFENDER_PASSWORD="mypassword"
python script.pye

# Windows (Command Prompt)
set STXDEFENDER_PASSWORD=mypassword
python script.pye

# Windows (PowerShell)
$env:STXDEFENDER_PASSWORD="mypassword"
python script.pye
```

If the environment variable is not set, it will use the password embedded in the file (or the one you specified during encryption).

## Trial Mode

Without a valid license activation, STXDefender operates in trial mode:

- ✅ Encryption works normally
- ⚠️ Maximum TTL is limited to 24 hours
- ⚠️ A warning message is displayed

To remove trial limitations, activate with a valid token from the dashboard.

## Project Structure

```
.
├── backend/
│   └── app.py              # Flask backend API
├── frontend/
│   ├── index.html          # Landing page
│   ├── login.html          # Login/signup page
│   ├── dashboard.html      # User dashboard
│   ├── admin.html          # Admin dashboard
│   └── static/
│       ├── style.css       # Styles
│       ├── auth.js         # Auth page JavaScript
│       ├── dashboard.js    # Dashboard JavaScript
│       └── admin.js        # Admin panel JavaScript
├── stxdefender.py          # Main CLI tool
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup for PyPI
└── README.md              # This file
```

## Development

### Running the Backend

**Windows:**
- Use `setup_and_run.bat` (installs and runs)
- Use `START.bat` (quick start)
- Use `run_server.bat` (assumes dependencies installed)

**Linux/Mac:**
```bash
./setup_and_run.sh
# OR
cd backend
python3 app.py
```

The server runs on `http://localhost:5000` by default.

### Environment Variables

- `STXDEFENDER_API_URL` - API endpoint URL (default: `http://localhost:5000`)
- `SECRET_KEY` - Flask secret key (default: auto-generated)
- `STXDEFENDER_PASSWORD` - Default password for encrypted files

### Database

The backend uses SQLite by default (`jsdefender.db` for compatibility). For production deployments, consider using PostgreSQL or MySQL.

## Security

STXDefender implements multiple layers of security:

- **Strong Encryption**: AES-256-GCM authenticated encryption prevents tampering
- **Key Derivation**: PBKDF2 with 200,000 iterations for key generation
- **Secure Tokens**: Cryptographically secure random token generation
- **License Binding**: System fingerprinting binds licenses to specific machines
- **Dual Validation**: Both local and remote license validation
- **Password Security**: Passwords are hashed using SHA-256 (bcrypt recommended for production)

## Use Cases

- Protect proprietary Python applications
- Distribute encrypted scripts with expiration dates
- Control access to sensitive code
- License management for commercial software
- Secure distribution of Python tools and utilities

## License

This project is provided as-is for educational and development purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For issues and questions, please open an issue on the project repository.
