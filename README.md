# Instagram Saved Videos Downloader

A simple and easy-to-use tool for downloading saved videos from Instagram.

## Features

- Automatically retrieves Instagram login credentials from Firefox browser
- Downloads videos from your saved Instagram posts
- Automatically filters out non-video content
- Maintains download records to avoid duplicates
- Simple command-line interface

## Installation

### Prerequisites

- Python 3.6+
- Firefox browser (for cookies)
- Instagram account logged in on Firefox

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/insDownloader.git
cd insDownloader

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Start the program
python main.py
```

The program will provide the following options:
1. Login/Change Account
2. Download Saved Videos
3. Exit

### Tips

- For first-time use, select "Login/Change Account" to ensure your account is properly set up
- Downloaded videos will be saved in the `downloads` directory
- Download records are stored in the `logs` directory to prevent duplicate downloads

## Project Structure

```
insDownloader/
├── main.py           # Production environment main program
├── login.py          # Login functionality module
├── download.py       # Download functionality module
├── test_main.py      # Test environment main program
├── test_login.py     # Test environment login module
├── test_download.py  # Test environment download module
├── deploy.py         # Deployment script
└── rollback.py       # Rollback script
```

## Creating Executable File

You can use PyInstaller to package this program as a standalone .exe file that doesn't require Python installation:

```bash
# Install PyInstaller
pip install pyinstaller

# Package the application
pyinstaller --onefile --icon=icon.ico main.py

# Or create a single-file version with dependencies
pyinstaller --onefile --icon=icon.ico --name="InsDownloader" main.py
```

The packaged .exe file will be located in the `dist` directory and can be distributed directly to users.

### Packaging Notes

- Ensure you complete testing and deploy to production version before packaging
- Use the `--noconsole` parameter to hide the console window (not recommended, may hide important error messages)
- You can add a custom icon to make the application look more professional

## Privacy and Security

- This tool only uses your login information locally and does not send it to any third parties
- Login information is stored in local session files
- We recommend regularly updating your Instagram password to ensure account security

## Contributing

Feel free to submit issues and suggestions for improvements! Please contribute via GitHub Issues or Pull Requests.

## License

[MIT License](LICENSE)
