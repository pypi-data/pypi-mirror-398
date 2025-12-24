import sys
import os
import re
from google import genai
from scanner import get_project_data
from generator import create_prompt
import threading
import itertools
import time

def clean_markdown(markdown_text):
    """Clean and format the generated markdown for better readability"""
    if not markdown_text:
        return ""
    
    # Remove any markdown code block wrappers if AI wrapped the entire response
    text = markdown_text.strip()
    if text.startswith('```') and text.endswith('```'):
        # Extract content from markdown code block
        lines = text.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines)
    
    lines = text.split('\n')
    cleaned_lines = []
    prev_empty = False
    in_code_block = False
    
    for i, line in enumerate(lines):
        # Track code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            # Ensure blank line before code block (unless at start)
            if not in_code_block and cleaned_lines and cleaned_lines[-1].strip():
                cleaned_lines.append('')
            cleaned_lines.append(line)
            prev_empty = False
            continue
        
        # Inside code blocks, preserve everything
        if in_code_block:
            cleaned_lines.append(line)
            continue
        
        # Remove excessive empty lines (max 2 consecutive)
        if not line.strip():
            if not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
            continue
        
        prev_empty = False
        
        # Ensure proper spacing before headers (except at start)
        if line.strip().startswith('#'):
            if cleaned_lines and cleaned_lines[-1].strip() and not cleaned_lines[-1].startswith('#'):
                cleaned_lines.append('')
        
        cleaned_lines.append(line)
    
    # Join and clean up
    result = '\n'.join(cleaned_lines)
    
    # Remove triple or more newlines
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # Ensure proper spacing after headers (header followed by non-header should have blank line)
    result = re.sub(r'(#{1,6} .+?)\n([^#\n])', r'\1\n\n\2', result)
    
    # Fix code blocks without proper closing
    result = re.sub(r'```(\w+)?\n([^`]+?)(\n```|$)', lambda m: f'```{m.group(1) or ""}\n{m.group(2)}\n```', result, flags=re.DOTALL)
    
    # Remove trailing whitespace from each line
    result = '\n'.join(line.rstrip() for line in result.split('\n'))
    
    # Ensure file ends with single newline
    return result.strip() + '\n'

def print_banner():
    """Print a cool banner"""
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
    banner = """
╔═══════════════════════════════════════════════════════╗
║     🚀  README GENERATOR - Auto Documentation  🚀     ║
║         Analyze your project & generate README        ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)

def animate_spinner(stop_event, message="Thinking"):
    """Animated spinner for loading states"""
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    for c in itertools.cycle(spinner_chars):
        if stop_event.is_set():
            break
        sys.stdout.write(f'\r{message} {c} ')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(message) + 3) + '\r')

def get_api_key():
    """Get API key from environment variable or prompt user"""
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    
    if not api_key:
        print("\n" + "="*60)
        print("⚠️  API KEY REQUIRED")
        print("="*60)
        print("API Key not found in environment variables.")
        print("\nOptions:")
        print("1. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
        print("2. Enter your API key now (it won't be saved)")
        print("\nGet your API key from: https://makersuite.google.com/app/apikey")
        print("="*60)
        api_key = input("\nEnter API Key: ").strip()
        
        if not api_key:
            print("\n❌ Error: API key is required to use this tool.")
            sys.exit(1)
    
    return api_key

def run_tool():
    print_banner()
    
    # Get API key
    try:
        api_key = get_api_key()
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ Error initializing API client: {e}")
        return
    
    # Handle the target path
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        print("\n" + "-"*60)
        print("📁 PROJECT FOLDER")
        print("-"*60)
        target_path = input("Enter project folder path (or press Enter for current directory): ").strip()
        if not target_path:
            target_path = '.'
        print()
    
    # Check if folder actually exists
    if not os.path.exists(target_path):
        print("\n" + "="*60)
        print("❌ ERROR")
        print("="*60)
        print(f"The folder '{target_path}' does not exist.")
        print("="*60)
        return
    
    if not os.path.isdir(target_path):
        print("\n" + "="*60)
        print("❌ ERROR")
        print("="*60)
        print(f"'{target_path}' is not a directory.")
        print("="*60)
        return
    
    # Scan project
    print("\n" + "="*60)
    print("🔍 SCANNING PROJECT")
    print("="*60)
    print(f"Path: {os.path.abspath(target_path)}")
    print("Analyzing files, dependencies, and structure...")
    
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=animate_spinner, args=(stop_spinner, "Scanning"))
    spinner_thread.start()
    
    try:
        project_info = get_project_data(target_path)
        stop_spinner.set()
        spinner_thread.join()
        
        # Display scan results
        print("\n" + "="*60)
        print("✅ SCAN COMPLETE")
        print("="*60)
        tech_display = ', '.join(project_info['tech']) if project_info['tech'] else 'None detected'
        print(f"📦 Technologies: {tech_display}")
        print(f"📝 Files analyzed: {len(project_info['file_summaries'])}")
        if project_info['entry_points']:
            print(f"🎯 Entry points: {', '.join(project_info['entry_points'])}")
        if project_info['package_manager']:
            print(f"📦 Package manager: {project_info['package_manager']}")
        print("="*60)
        
    except Exception as e:
        stop_spinner.set()
        spinner_thread.join()
        print("\n" + "="*60)
        print("❌ ERROR")
        print("="*60)
        print(f"Error scanning project: {e}")
        print("="*60)
        return
    
    # Ask for optional context
    print("\n" + "-"*60)
    print("💡 OPTIONAL CONTEXT")
    print("-"*60)
    print("Provide additional context about your project")
    print("Example: 'A web scraper for e-commerce sites'")
    print("         'A REST API for task management'")
    user_context = input("\nContext (press Enter to skip): ").strip()
    project_info['user_goal'] = user_context if user_context else None
    
    # Generate README
    print("\n" + "="*60)
    print("🧠 GENERATING README")
    print("="*60)
    print("This may take a moment...\n")
    
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=animate_spinner, args=(stop_spinner, "Generating"))
    spinner_thread.start()
    
    try:
        user_prompt = create_prompt(project_info)
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=user_prompt
        )
        
        stop_spinner.set()
        spinner_thread.join()
        
        # Save the README
        output_file = os.path.join(target_path, "README.md")
        
        # Check if README already exists
        if os.path.exists(output_file):
            print("\n" + "⚠️"*30)
            print(f"⚠️  WARNING: README.md already exists!")
            print(f"⚠️  Location: {os.path.abspath(output_file)}")
            print("⚠️"*30)
            overwrite = input("\nOverwrite existing file? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("\n❌ Operation cancelled. README not generated.")
                return
            print()
        
        # Clean and format the markdown
        cleaned_markdown = clean_markdown(response.text)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_markdown)
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"📄 Location: {os.path.abspath(output_file)}")
        print(f"📊 Size: {len(cleaned_markdown)} characters")
        print(f"📏 Lines: {len(cleaned_markdown.split(chr(10)))}")
        print("="*60)
        
    except Exception as e:
        stop_spinner.set()
        spinner_thread.join()
        print("\n" + "="*60)
        print("❌ ERROR")
        print("="*60)
        print(f"Error generating README: {e}")
        if "API key" in str(e) or "authentication" in str(e).lower():
            print("\n💡 Tip: Check your API key and try again.")
            print("   Get your API key from: https://makersuite.google.com/app/apikey")
        print("="*60)
        return

if __name__ == "__main__":
    try:
        run_tool()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)