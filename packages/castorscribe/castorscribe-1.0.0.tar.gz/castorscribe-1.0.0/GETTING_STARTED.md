# Getting Started - First Time User Guide

Welcome! This guide will help you use `readme-gen` for the first time.

## Step 1: Install the Package

```bash
pip install readme-gen
```

## Step 2: Get Your API Key

You need a free Google Gemini API key to generate READMEs:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (it looks like: `AIza...`)

## Step 3: Set Your API Key (Choose One Method)

### Option A: Set Environment Variable (Recommended - Permanent)

**Windows (Command Prompt):**
```cmd
setx GEMINI_API_KEY "your_api_key_here"
```
Then close and reopen your terminal.

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'your_api_key_here', 'User')
```
Then close and reopen your terminal.

**Linux/Mac:**
```bash
echo 'export GEMINI_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### Option B: Enter When Prompted (Temporary)

If you don't set the environment variable, the tool will ask you for the API key each time you run it.

## Step 4: Generate Your First README

Navigate to your project folder and run:

```bash
# If you're already in your project folder
readme-gen

# Or specify the path to your project
readme-gen C:\path\to\your\project
```

## What Happens Next?

1. The tool scans your project folder
2. It detects technologies, dependencies, and code structure
3. It asks if you want to provide any additional context (optional)
4. It generates a professional README.md file in your project folder
5. Done! Check your `README.md` file

## Example

```bash
# Navigate to your project
cd C:\Users\YourName\projects\my-awesome-app

# Generate README
readme-gen

# The tool will:
# - Scan your project
# - Ask for API key (if not set)
# - Ask for project path (if not provided)
# - Ask for optional context
# - Generate README.md
```

## Troubleshooting

**"Command not found" after installation:**
- Make sure Python Scripts folder is in your PATH
- Try: `python -m main` instead

**"API key not found":**
- Make sure you set the environment variable correctly
- Restart your terminal after setting it
- Or enter it when prompted

**"Project folder not found":**
- Use the full path: `readme-gen C:\full\path\to\project`
- Or navigate to the project first: `cd project_folder` then `readme-gen`

## Need More Help?

- See [QUICKSTART.md](QUICKSTART.md) for a condensed guide
- Check [README.md](README.md) for full documentation
- Review [INSTALL.md](INSTALL.md) for detailed installation options

