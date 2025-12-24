def create_prompt(project_info):
    """Create a comprehensive prompt for AI to generate an awesome README"""
    
    # Format file summaries
    file_summaries_text = ""
    for file_info in project_info['file_summaries'][:20]:  # Limit to 20 files
        file_summaries_text += f"\n--- {file_info['path']} ---\n"
        file_summaries_text += f"{file_info['content'][:800]}\n"
    
    # Format dependencies
    deps_text = ""
    if project_info['dependencies']['python']:
        deps_text += f"\nPython Dependencies:\n" + "\n".join(f"  - {dep}" for dep in project_info['dependencies']['python'][:15])
    if project_info['dependencies']['node']:
        deps_text += f"\nNode.js Dependencies:\n" + "\n".join(f"  - {dep}" for dep in project_info['dependencies']['node'][:15])
    
    # Format tech stack
    tech_stack_text = ", ".join(project_info['tech']) if project_info['tech'] else "Unknown"
    
    # Format entry points
    entry_points_text = "\n".join(f"  - {ep}" for ep in project_info['entry_points']) if project_info['entry_points'] else "  - Not detected"
    
    prompt = f"""You are an expert technical writer specializing in creating professional, comprehensive, and engaging README.md files for software projects.

TASK: Generate a complete, production-ready README.md file based on the project analysis below.

PROJECT INFORMATION:
- Project Name: {project_info['name']}
- Technology Stack: {tech_stack_text}
- Package Manager: {project_info['package_manager'] or 'Not detected'}
- Entry Points: 
{entry_points_text}
- Has Existing README: {project_info['has_readme']}
- Has License File: {project_info['has_license']}
- User's Goal/Context: {project_info.get('user_goal', 'Not provided')}

DEPENDENCIES DETECTED:
{deps_text if deps_text else "  - No dependencies file detected"}

PROJECT STRUCTURE:
```
{project_info['tree'] if project_info['tree'] else 'Structure not available'}
```

KEY FILES AND CONTENT:
{file_summaries_text if file_summaries_text else "No code files analyzed"}

REQUIREMENTS FOR THE README:

1. HEADER SECTION:
   - Create appropriate badges using shields.io format (e.g., ![Language](https://img.shields.io/badge/Language-Python-blue))
   - Include badges for: main technology, license (if detected), version if applicable
   - Add a catchy, descriptive title with an emoji
   - Write a compelling 2-3 sentence description

2. TABLE OF CONTENTS (if README is long):
   - Use markdown links to sections

3. FEATURES SECTION:
   - Analyze the code and structure to infer key features
   - List 3-5 main features
   - Be accurate - only mention features you can infer from the code

4. TECH STACK SECTION:
   - List all detected technologies
   - Briefly explain what each technology is used for in this project

5. INSTALLATION SECTION:
   - Provide clear step-by-step installation instructions
   - Include commands for cloning (if applicable)
   - Show how to install dependencies based on detected package manager
   - Include virtual environment setup if Python project
   - Add any environment variable setup if .env files are detected

6. USAGE SECTION:
   - Explain how to run the project
   - Include example commands
   - Show code examples if applicable
   - Reference the entry points detected

7. PROJECT STRUCTURE SECTION:
   - Include the file tree (already provided above)
   - Briefly explain key directories and files

8. CONFIGURATION (if applicable):
   - Mention configuration files if detected

9. CONTRIBUTING (optional):
   - Add a brief contributing section

10. LICENSE:
    - Mention license if detected, otherwise say "See LICENSE file" or "All rights reserved"

11. AUTHOR/CREDITS:
    - Generic placeholder for author information

CRITICAL FORMATTING REQUIREMENTS:
- Use proper markdown syntax - headers must use #, ##, ### correctly
- Code blocks MUST use triple backticks with language specification: ```python, ```bash, ```javascript, etc.
- Use proper spacing: one blank line before headers, one blank line after headers
- Lists must use proper markdown: - for unordered, 1. for ordered
- Inline code must use single backticks: `code`
- Links must use proper format: [text](url)
- Tables must use proper markdown table syntax with | separators
- Do NOT include any text before the badges - start immediately with the markdown
- Do NOT include explanations or comments - output ONLY the README markdown
- Ensure consistent formatting throughout
- Use proper line breaks - one blank line between sections

IMPORTANT GUIDELINES:
- Write in a professional yet friendly tone
- Include code blocks with syntax highlighting (specify language after ```)
- Make it visually appealing with emojis where appropriate (but don't overdo it - max 1-2 per section)
- Be accurate - don't invent features that aren't in the code
- If you're unsure about something, be generic rather than wrong
- Make the README comprehensive but not overwhelming
- Use clear, concise language
- Ensure all code examples are properly formatted with correct syntax highlighting

OUTPUT FORMAT:
Start immediately with badges (no preamble, no explanation, no "Here's the README:" text).
Output ONLY the markdown content that should go in README.md file.
Do not wrap it in code blocks or add any meta-commentary."""
    
    return prompt