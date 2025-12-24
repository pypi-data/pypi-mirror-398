![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![PyPI](https://img.shields.io/badge/pypi-readme--gen-blue)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

# Readme Generator ✨ Automated README Creation with AI

Readme Generator is a powerful Python-based tool designed to automatically create comprehensive and engaging `README.md` files for your software projects. Leveraging Google's Generative AI, it intelligently scans your project structure, detects technologies, identifies dependencies, and synthesizes a professional README tailored to your codebase.

## 🚀 Quick Start (New Users)

**Just installed? Follow these 3 steps:**

1. **Get your free API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Set the API key** (choose one):
   - **Windows:** `setx GEMINI_API_KEY "your_api_key_here"` (then restart terminal)
   - **Linux/Mac:** `export GEMINI_API_KEY='your_api_key_here'` (add to `~/.bashrc` for permanent)
3. **Generate README:**
   ```bash
   cd /path/to/your/project
   castorscribe
   ```

That's it! Your `README.md` will be created in your project folder.

> 📖 **New to the tool?** See [GETTING_STARTED.md](GETTING_STARTED.md) for a detailed first-time user guide.

## Table of Contents

- [Quick Start (New Users)](#-quick-start-new-users)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

## Features

- **Automated Project Analysis**: Scans your project directory to identify key files, programming languages, and frameworks.
- **Dependency Detection**: Automatically lists Python dependencies using `requirements.txt` or similar mechanisms.
- **AI-Powered README Generation**: Utilizes Google GenAI to craft a detailed and well-structured `README.md` based on the project's analysis.
- **Dynamic Content Generation**: Generates sections like Features, Tech Stack, Installation, Usage, and Project Structure tailored to your specific project.
- **Markdown Cleanup**: Formats and cleans the AI-generated markdown for optimal readability and adherence to best practices.

## Technology Stack

This project is built using the following technologies:

- **Python**: The core programming language that drives the entire application, from scanning to AI interaction.
- **Google GenAI**: Integrated to provide the advanced artificial intelligence capabilities for generating high-quality markdown content.

## Installation

### Quick Install (Recommended)

Install directly from PyPI:

```bash
pip install castorscribe
```

After installation, use it from anywhere:

```bash
# Generate README for current directory
castorscribe

# Generate README for specific folder
castorscribe /path/to/your/project
```

### Alternative: Install from Source

If you want to install from source:

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/readme-generator.git
    cd readme-generator
    ```

2.  **Install the package**:

    ```bash
    pip install -e .
    ```

    Or install dependencies only:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

This project requires a Google Gemini API key to function.

### Get Your API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to generate your API key
2. Copy your API key

### Set the API Key

The application looks for the API key in these environment variables (in order):
- `GEMINI_API_KEY` (preferred)
- `GOOGLE_API_KEY`

#### Windows (Permanent)

```cmd
setx GEMINI_API_KEY "your_api_key_here"
```

Then restart your terminal.

#### Windows (Temporary - Current Session)

**Command Prompt:**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**PowerShell:**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

#### Linux/Mac (Permanent)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export GEMINI_API_KEY='your_api_key_here'
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### Linux/Mac (Temporary - Current Session)

```bash
export GEMINI_API_KEY='your_api_key_here'
```

**Note**: If the API key is not set, the tool will prompt you to enter it when you run it.

## Usage

### Basic Usage

After installation, you can use the `castorscribe` command from anywhere:

```bash
# Generate README for current directory
castorscribe

# Generate README for a specific project folder
castorscribe /path/to/your/project

# Alternative command name
generate-readme /path/to/your/project
```

### Running from Source

If installed from source without the entry point:

```bash
python main.py /path/to/your/project
```

The generated `README.md` file will be created in the specified project directory.

## Project Structure

```
├── README.md
├── generator.py
├── main.py
├── requirements.txt
└── scanner.py

```

-   `main.py`: The primary entry point for the application. It orchestrates the scanning, AI interaction, and final README generation process.
-   `scanner.py`: Responsible for analyzing the target project's file system, detecting technologies, dependencies, and extracting relevant code snippets for the AI prompt.
-   `generator.py`: Contains the logic for constructing a comprehensive prompt for the AI model based on the data gathered by `scanner.py`.
-   `requirements.txt`: Lists all Python package dependencies required to run the Readme Generator.
-   `README.md`: This file, generated by the tool itself or a placeholder for the generated output.

## Contributing

Contributions are welcome! If you have suggestions for improving the Readme Generator, please feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

-   Your Name / Organization
