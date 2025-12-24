# Quick Start Guide

Get started with README Generator in 3 simple steps!

## Step 1: Install

```bash
pip install readme-gen
```

## Step 2: Set API Key

Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Windows:**
```cmd
setx GEMINI_API_KEY "your_api_key_here"
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY='your_api_key_here'
# Add to ~/.bashrc or ~/.zshrc for permanent setup
```

## Step 3: Generate README

```bash
# For current directory
readme-gen

# For specific project
readme-gen /path/to/your/project
```

That's it! Your README.md will be generated in the project folder.

## Example

```bash
# Navigate to your project
cd ~/projects/my-awesome-project

# Generate README
readme-gen

# Done! Check README.md
```

## Need Help?

- **First time user?** See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed step-by-step instructions
- Check the full [README.md](README.md) for detailed documentation
- See [INSTALL.md](INSTALL.md) for installation options
- Read [PUBLISH.md](PUBLISH.md) if you want to publish your own version

