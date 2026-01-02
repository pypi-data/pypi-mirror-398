# STXDefender - Python Source Code Encryption Tool

STXDefender is the easiest way to obfuscate Python code using AES-256-GCM encryption. AES is a symmetric algorithm which uses the same key for both encryption and decryption (the security of an AES system increases exponentially with key length). There is no impact on the performance of your running application as the decryption process takes place during the import of your module, so encrypted code won't run any slower once loaded from a `.pye` file compared to loading from a `.py` or `.pyc` file.

## Features

- ✅ **No end-user device licence required** - Encrypted files run independently
- ✅ **Symmetric AES-256-GCM encryption** - Industry-standard authenticated encryption
- ✅ **FIPS 140-2 compliant cryptography** - Military-grade security standards
- ✅ **Enforced expiry time on encrypted code** - Control access with TTL
- ✅ **License Activation** - Secure token-based activation system with online validation
- ✅ **Custom Password Support** - Use your own passwords or auto-generated secure keys
- ✅ **Trial Mode** - Test the tool with 24-hour encrypted file limits
- ✅ **Bundle encrypted files using PyInstaller** - Full integration support
- ✅ **Web Dashboard** - Manage licenses, tokens, and subscriptions through a modern web interface

## Supported Environments

We support the following Operating System and architecture combinations. Encrypted code will run on ANY other target using the same version of Python. For example, files encrypted in Windows using Python 3.10 will run with Python 3.10 on Linux.

| CPU Architecture | Operating System | Python Architecture | Python Versions |
|-----------------|------------------|---------------------|-----------------|
| AMD64           | Windows          | 64-bit              | 3.8 - 3.12      |
| x86_64          | Linux            | 64-bit              | 3.8 - 3.12      |
| x86_64          | macOS            | 64-bit              | 3.8 - 3.12      |
| ARM64           | macOS            | 64-bit              | 3.8 - 3.12      |
| AARCH64         | Linux            | 64-bit              | 3.8 - 3.12      |

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

## Trial Licence

The installation of STXDefender will grant you a trial licence to encrypt files. This trial licence will only allow your script to work for a maximum of 24 hours; after that, it won't be usable. This is so you can test whether our solution is suitable for your needs.

## Subscribe & Activate

To distribute encrypted code without limitation, you will need to create an account and set up your subscription. Once you have set up the account, you will be able to retrieve your activation token and use it to authorise your installation:

```bash
$ stxdefender activate --token 470a7f2e76ac11eb94390242ac130002
STXDEFENDER ACTIVATED

Registration:

 - Account Status  : Active
 - Email Address   : hello@example.com
 - Account ID      : bfa41ccd-9738-33c0-83e9-cfa649c05288
 - System ID       : 7c9d-6ebb-5490-4e6f
 - Valid Until     : Sun, Apr 9, 2025 10:59 PM
```

Without activating your SDK, any encrypted code you create will only be usable for a maximum of 24hrs. Access to our dashboard (via HTTPS) from your system is required so we can validate your account status.

If you want to view your activated licence status, you can use the validate option:

```bash
$ stxdefender validate
STXDEFENDER

Registration:

 - Account Status  : Active
 - Email Address   : hello@example.com
 - Account ID      : bfa41ccd-9738-33c0-83e9-cfa649c05288
 - System ID       : 7c9d-6ebb-5490-4e6f
 - Valid Until     : Sun, Apr 9, 2025 10:59 PM
$
```

If your licence is valid, this command will give the Exit Code (EC) of #0 (zero); otherwise, an invalid licence will be indicated by the EC of #1 (one). You should run this command after any automated build tasks to ensure you haven't created code with an unexpected 24-hour limitation.

## Usage

We have worked hard to ensure that the encryption/decryption process is as simple as possible. Here are a few examples of how it works and how to use the features provided.

### How do I protect my Python source code?

First, let's have a look at an example of the encryption process:

```bash
$ cat /home/ubuntu/helloworld.py
print("Hello World!")
$
```

This is a very basic example, but we do not want anyone to get at our source code. We also don't want anyone to run this code after 1 hour so when we encrypt the file we can enforce an expiry time of 1 hour from now with the `--ttl` option, and we can delete the plaintext `.py` file after encryption by adding the `--remove` option.

The command would look like this:

```bash
$ stxdefender encrypt --remove --ttl=1h /home/ubuntu/helloworld.py
STXDEFENDER

Processing:

  /home/ubuntu/helloworld.py

Encrypted → /home/ubuntu/helloworld.pye
TTL enforced: 1h
Original /home/ubuntu/helloworld.py removed
$
```

The TTL argument offers the following options: weeks(w), days(d), hours(h), minutes(m), and seconds(s). Usage is for example: `--ttl=10s`, or `--ttl=24m`, or `--ttl=1d`, or just `--ttl=3600`. This can't be changed after encryption.

The `--remove` option deletes the original `.py` file. Make sure you use this so you don't accidentally distribute the plain-text code.

### Importing packages & modules

The usual import system can still be used, and you can import encrypted code from within encrypted code, so you don't need to do anything special with your import statements. However, you need to import the `stxdefender` module before importing encrypted code.

```bash
$ cd /home/ubuntu
$ ls
helloworld.pye
$ python3
>>>
>>> import stxdefender
>>> import helloworld
Hello World!
>>> exit()
$
```

**Note:** When using encrypted files, you must import `stxdefender` before importing any encrypted `.pye` modules. This registers the import hook that handles decryption.

### Using your own password for encryption

It's easy to use your own encryption password. If you do not set this, we generate unique ones for each file you encrypt. Our passwords are more secure, but should you wish to set your own, these can be set from a command option:

```bash
stxdefender encrypt --password=1234abcd mycode.py
```

or as an Environment variable:

```bash
export STXDEFENDER_PASSWORD="1234abcd"
stxdefender encrypt mycode.py
```

To import the code, you can set an environment variable (as with the encryption process). You can also set these in your code before the import:

```bash
$ python3
>>> import stxdefender
>>> from os import environ
>>> environ["STXDEFENDER_PASSWORD"] = "1234abcd"
>>> import mycode
```

The password is applicable to the next import, so if you want different ones for different files, feel free to encrypt with different values.

### How do shebangs work with encrypted files?

You can add a shebang to encrypted `.pye` files to make them directly executable. The shebang must be the first line of the file, followed by the encrypted content.

**Important:** Normal Python imports (`import module`) always require the `.pye` extension. Files without extension are only recognized when executed directly (via `./script` or `python script`), not when imported.

Here's an example. First, encrypt a file:

```bash
$ cat echo.py
print("echo")
print("Name:", __name__)
$ stxdefender encrypt echo.py --remove
$ sed -i '1i#!/usr/bin/env python3' echo.pye
$ chmod +x echo.pye
$ ./echo.pye
echo
Name: __main__
$
```

On Windows, you can use Python directly:

```bash
python echo.pye
```

### Integrating encrypted code with PyInstaller

PyInstaller scans your plain-text code for import statements so it knows what packages to freeze. When using encrypted code, ensure that STXDefender is included in your dependencies and that you import it before any encrypted modules.

For this example, we have the following project structure:

```
pyexe.py
lib
└── helloworld.pye
```

In our pyexe script, we have the following code:

```bash
$ cat pyexe.py
import stxdefender
import helloworld
```

To ensure that PyInstaller includes our encrypted files, we need to tell it where they are with the `--add-binary` option. So, for the above project, we could use this command:

```bash
stxdefender encrypt pyexe.py --remove
pyinstaller --add-binary "lib/helloworld.pye:lib" pyexe.pye
```

Make sure to include `stxdefender` in your `requirements.txt` or `pyinstaller` dependencies so that the decryption module is available in the bundled executable.

### Integrating encrypted code with Django

You can encrypt your Django project just the same as you can any other Python code. Don't forget to include `import stxdefender` in the `__init__.py` file that is in the same directory as your `settings.py` file. Only encrypt your own code and not code generated by the Django commands. There is no point in protecting files such as `urls.py` as these should not contain much/any of your own code other than things that have been imported.

## Command Reference

### `stxdefender activate --token <token>`

Activate your license with a token obtained from the dashboard.

```bash
stxdefender activate --token 470a7f2e76ac11eb94390242ac130002
```

### `stxdefender validate`

Check your current license activation status. Returns exit code 0 if valid, 1 if invalid.

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

## Environment Variables

- `STXDEFENDER_API_URL` - API endpoint URL (default: `http://localhost:5000`)
- `STXDEFENDER_PASSWORD` - Default password for encrypted files

## Development

### Running the Backend

If you installed from source and want to run your own server:

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

### Database

The backend uses SQLite by default (`jsdefender.db` for compatibility). For production deployments, consider using PostgreSQL or MySQL.

## Security

STXDefender implements multiple layers of security:

- **Strong Encryption**: AES-256-GCM authenticated encryption prevents tampering
- **Key Derivation**: PBKDF2 with 200,000 iterations for key generation
- **FIPS 140-2 Compliance**: Uses cryptography libraries compliant with FIPS standards
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

THE SOFTWARE IS PROVIDED "AS IS," AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE. REVERSE ENGINEERING IS STRICTLY PROHIBITED.

This project is provided as-is for educational and development purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For issues and questions, please open an issue on the project repository.
