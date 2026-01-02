#!/usr/bin/env python3
"""
LaTeX Resume MCP Server
Create, edit, and compile LaTeX resumes directly from Claude.
"""

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("latex-resume")

# Configurable directories via environment variables
def get_resumes_dir() -> Path:
    """Get the resumes directory from env or default."""
    default = Path.home() / ".latex-resumes" / "resumes"
    return Path(os.environ.get("LATEX_RESUME_DIR", default))

def get_templates_dir() -> Path:
    """Get the templates directory from env or default."""
    default = Path.home() / ".latex-resumes" / "templates"
    return Path(os.environ.get("LATEX_TEMPLATES_DIR", default))

# LaTeX Resume Templates
LATEX_TEMPLATES = {
    "modern": r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{xcolor}

\geometry{left=0.75in, right=0.75in, top=0.5in, bottom=0.5in}
\pagestyle{empty}

% Colors
\definecolor{primary}{RGB}{0, 79, 144}
\definecolor{secondary}{RGB}{89, 89, 89}

% Section formatting
\titleformat{\section}{\large\bfseries\color{primary}}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{12pt}{6pt}

% Custom commands
\newcommand{\resumeItem}[1]{\item\small{#1}}
\newcommand{\resumeSubheading}[4]{
  \item
    \begin{tabular*}{\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small#4} \\
    \end{tabular*}\vspace{-5pt}
}

\begin{document}

% Header
\begin{center}
    {\LARGE\bfseries YOUR NAME}\\[4pt]
    \href{mailto:email@example.com}{email@example.com} $|$
    (123) 456-7890 $|$
    \href{https://linkedin.com/in/yourprofile}{LinkedIn} $|$
    \href{https://github.com/yourusername}{GitHub}
\end{center}

\section{Experience}
\begin{itemize}[leftmargin=0.15in, label={}]
\resumeSubheading
    {Company Name}{City, State}
    {Job Title}{Start Date -- End Date}
    \begin{itemize}[leftmargin=0.2in]
        \resumeItem{Accomplishment or responsibility}
        \resumeItem{Another accomplishment}
    \end{itemize}
\end{itemize}

\section{Education}
\begin{itemize}[leftmargin=0.15in, label={}]
\resumeSubheading
    {University Name}{City, State}
    {Degree, Major}{Graduation Date}
\end{itemize}

\section{Skills}
\begin{itemize}[leftmargin=0.15in, label={}]
    \item \textbf{Programming:} Python, JavaScript, Java, C++
    \item \textbf{Tools:} Git, Docker, AWS, Linux
\end{itemize}

\end{document}
""",
    "classic": r"""\documentclass[11pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{enumitem}

\geometry{margin=1in}
\pagestyle{empty}

\begin{document}

\begin{center}
    {\Large\textbf{YOUR NAME}}\\[6pt]
    Address Line $\bullet$ City, State ZIP\\
    Phone: (123) 456-7890 $\bullet$ Email: email@example.com
\end{center}

\vspace{12pt}

\noindent\textbf{\large OBJECTIVE}\\
\rule{\textwidth}{0.4pt}\\[3pt]
A brief statement about your career objectives.

\vspace{12pt}

\noindent\textbf{\large EDUCATION}\\
\rule{\textwidth}{0.4pt}\\[3pt]
\textbf{University Name} \hfill City, State\\
Degree, Major \hfill Graduation Date\\
GPA: X.XX

\vspace{12pt}

\noindent\textbf{\large EXPERIENCE}\\
\rule{\textwidth}{0.4pt}\\[3pt]
\textbf{Company Name} \hfill City, State\\
\textit{Job Title} \hfill Start Date -- End Date
\begin{itemize}[leftmargin=0.2in, topsep=0pt]
    \item Accomplishment or responsibility
    \item Another accomplishment
\end{itemize}

\vspace{12pt}

\noindent\textbf{\large SKILLS}\\
\rule{\textwidth}{0.4pt}\\[3pt]
\textbf{Technical:} List of technical skills\\
\textbf{Languages:} Languages you speak

\end{document}
""",
    "minimal": r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.75in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}

\pagestyle{empty}
\setlength{\parindent}{0pt}

\begin{document}

\textbf{\Large YOUR NAME}\\[4pt]
email@example.com $|$ (123) 456-7890 $|$ City, State

\vspace{12pt}
\textbf{Experience}\hrulefill\\[6pt]
\textbf{Job Title}, Company Name \hfill Dates\\
\begin{itemize}[leftmargin=0.15in, topsep=0pt, parsep=0pt]
\item Accomplishment
\end{itemize}

\vspace{8pt}
\textbf{Education}\hrulefill\\[6pt]
\textbf{Degree}, University Name \hfill Graduation Date

\vspace{8pt}
\textbf{Skills}\hrulefill\\[6pt]
Skill 1, Skill 2, Skill 3

\end{document}
""",
}


def ensure_dirs():
    """Ensure resume and template directories exist."""
    get_resumes_dir().mkdir(parents=True, exist_ok=True)
    get_templates_dir().mkdir(parents=True, exist_ok=True)


def ensure_tex_extension(filename: str) -> str:
    """Ensure filename has .tex extension."""
    return filename if filename.endswith(".tex") else f"{filename}.tex"


def find_pdflatex() -> str | None:
    """Find pdflatex executable."""
    # Check PATH first
    pdflatex = shutil.which("pdflatex")
    if pdflatex:
        return pdflatex

    # Check common installation locations
    common_paths = [
        "/Library/TeX/texbin/pdflatex",  # MacTeX
        "/usr/local/texlive/2024/bin/x86_64-linux/pdflatex",  # TeX Live Linux
        "/usr/local/texlive/2024/bin/universal-darwin/pdflatex",  # TeX Live macOS
        "/usr/bin/pdflatex",  # System install
    ]

    for path in common_paths:
        if Path(path).exists():
            return path

    return None


@mcp.tool()
def list_resumes() -> str:
    """
    List all LaTeX resume files in the resumes directory.
    Returns filename, last modified date, and file size for each resume.
    """
    ensure_dirs()
    resumes_dir = get_resumes_dir()

    resumes = []
    for file in resumes_dir.glob("*.tex"):
        stats = file.stat()
        resumes.append({
            "filename": file.name,
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "size": stats.st_size
        })

    if not resumes:
        return json.dumps({
            "message": "No resume files found. Use create_resume to create one.",
            "resumes": [],
            "directory": str(resumes_dir)
        })

    return json.dumps({"count": len(resumes), "resumes": resumes, "directory": str(resumes_dir)}, indent=2)


@mcp.tool()
def read_resume(filename: str) -> str:
    """
    Read the contents of a LaTeX resume file.

    Args:
        filename: Name of the resume file (with or without .tex extension)

    Returns the full LaTeX content of the resume.
    """
    ensure_dirs()
    filepath = get_resumes_dir() / ensure_tex_extension(filename)

    if not filepath.exists():
        return json.dumps({"error": f"Resume '{filename}' not found"})

    try:
        content = filepath.read_text(encoding="utf-8")
        return content
    except Exception as e:
        return json.dumps({"error": f"Error reading file: {str(e)}"})


@mcp.tool()
def create_resume(filename: str, content: str = None, template: str = "modern") -> str:
    """
    Create a new LaTeX resume file.

    Args:
        filename: Name for the new resume file (with or without .tex extension)
        content: Full LaTeX content for the resume. If not provided, uses a template.
        template: Template to use if content not provided. Options: 'modern', 'classic', 'minimal'

    Returns confirmation of file creation.
    """
    ensure_dirs()
    filepath = get_resumes_dir() / ensure_tex_extension(filename)

    if filepath.exists():
        return json.dumps({"error": f"Resume '{filename}' already exists. Use edit_resume to modify it."})

    if content:
        resume_content = content
    elif template in LATEX_TEMPLATES:
        resume_content = LATEX_TEMPLATES[template]
    else:
        return json.dumps({"error": f"Unknown template '{template}'. Available: modern, classic, minimal"})

    try:
        filepath.write_text(resume_content, encoding="utf-8")
        return json.dumps({"success": True, "path": str(filepath), "template_used": template if not content else "custom"})
    except Exception as e:
        return json.dumps({"error": f"Error creating file: {str(e)}"})


@mcp.tool()
def edit_resume(filename: str, content: str = None, find: str = None, replace: str = None) -> str:
    """
    Edit an existing LaTeX resume file.

    Args:
        filename: Name of the resume file to edit
        content: New complete content for the resume (replaces everything)
        find: Text to find for targeted replacement (use with 'replace')
        replace: Text to replace the found text with

    Either provide 'content' for full replacement, or 'find' and 'replace' for targeted edit.
    """
    ensure_dirs()
    filepath = get_resumes_dir() / ensure_tex_extension(filename)

    if not filepath.exists():
        return json.dumps({"error": f"Resume '{filename}' not found"})

    try:
        if content:
            filepath.write_text(content, encoding="utf-8")
            return json.dumps({"success": True, "path": str(filepath), "edit_type": "full_replacement"})
        elif find is not None and replace is not None:
            current_content = filepath.read_text(encoding="utf-8")
            if find not in current_content:
                return json.dumps({"error": f"Could not find the specified text in {filename}"})
            new_content = current_content.replace(find, replace)
            filepath.write_text(new_content, encoding="utf-8")
            return json.dumps({"success": True, "path": str(filepath), "edit_type": "find_replace"})
        else:
            return json.dumps({"error": "Must provide either 'content' for full replacement or 'find' and 'replace' for targeted edit."})
    except Exception as e:
        return json.dumps({"error": f"Error editing file: {str(e)}"})


@mcp.tool()
def delete_resume(filename: str) -> str:
    """
    Delete a LaTeX resume file.

    Args:
        filename: Name of the resume file to delete
    """
    ensure_dirs()
    filepath = get_resumes_dir() / ensure_tex_extension(filename)

    if not filepath.exists():
        return json.dumps({"error": f"Resume '{filename}' not found"})

    try:
        filepath.unlink()
        return json.dumps({"success": True, "deleted": str(filepath)})
    except Exception as e:
        return json.dumps({"error": f"Error deleting file: {str(e)}"})


@mcp.tool()
def compile_resume(filename: str, output_dir: str = None) -> str:
    """
    Compile a LaTeX resume to PDF using pdflatex.

    Args:
        filename: Name of the resume file to compile
        output_dir: Output directory for the PDF (default: same as resumes directory)

    Returns the path to the generated PDF or compilation errors.
    """
    ensure_dirs()
    resumes_dir = get_resumes_dir()
    filepath = resumes_dir / ensure_tex_extension(filename)

    if not filepath.exists():
        return json.dumps({"error": f"Resume '{filename}' not found"})

    pdflatex_cmd = find_pdflatex()
    if not pdflatex_cmd:
        return json.dumps({
            "error": "pdflatex not found. Please install LaTeX:",
            "install_instructions": {
                "macOS": "brew install --cask mactex  # or: brew install --cask basictex",
                "Ubuntu/Debian": "sudo apt install texlive-latex-base texlive-latex-extra",
                "Fedora": "sudo dnf install texlive-scheme-basic",
                "Windows": "Download from https://miktex.org/"
            }
        })

    out_dir = Path(output_dir) if output_dir else resumes_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Run pdflatex twice for proper reference resolution
        for _ in range(2):
            result = subprocess.run(
                [pdflatex_cmd, "-interaction=nonstopmode", f"-output-directory={out_dir}", filepath.name],
                cwd=resumes_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

        pdf_name = filepath.stem + ".pdf"
        pdf_path = out_dir / pdf_name

        if pdf_path.exists():
            # Clean up auxiliary files
            for ext in [".aux", ".log", ".out"]:
                aux_file = out_dir / (filepath.stem + ext)
                if aux_file.exists():
                    aux_file.unlink()

            return json.dumps({
                "success": True,
                "pdf_path": str(pdf_path),
                "message": f"Successfully compiled {filename} to PDF"
            })
        else:
            return json.dumps({
                "error": "Compilation failed",
                "stdout": result.stdout[-2000:] if result.stdout else "",
                "stderr": result.stderr[-2000:] if result.stderr else ""
            })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Compilation timed out after 60 seconds"})
    except Exception as e:
        return json.dumps({"error": f"Compilation error: {str(e)}"})


@mcp.tool()
def list_templates() -> str:
    """
    List available resume templates.
    Returns the names and descriptions of built-in LaTeX resume templates.
    """
    templates = {
        "modern": "Clean, professional design with color accents and structured formatting",
        "classic": "Traditional resume format with clear sections and horizontal rules",
        "minimal": "Simple, no-frills layout focusing on content"
    }
    return json.dumps(templates, indent=2)


@mcp.tool()
def get_template(template_name: str) -> str:
    """
    Get the content of a resume template.

    Args:
        template_name: Name of the template (modern, classic, minimal)

    Returns the full LaTeX template content.
    """
    if template_name not in LATEX_TEMPLATES:
        return json.dumps({"error": f"Template '{template_name}' not found. Available: modern, classic, minimal"})

    return LATEX_TEMPLATES[template_name]


@mcp.tool()
def add_experience(
    filename: str,
    company: str,
    title: str,
    dates: str,
    bullets: list[str],
    location: str = ""
) -> str:
    """
    Add a new work experience entry to a resume (works with modern template).

    Args:
        filename: Name of the resume file
        company: Company name
        title: Job title
        dates: Employment dates (e.g., 'Jan 2020 -- Present')
        bullets: List of bullet points describing responsibilities/achievements
        location: Location (city, state/country) - optional
    """
    ensure_dirs()
    filepath = get_resumes_dir() / ensure_tex_extension(filename)

    if not filepath.exists():
        return json.dumps({"error": f"Resume '{filename}' not found"})

    try:
        content = filepath.read_text(encoding="utf-8")

        bullet_items = "\n".join([f"        \\resumeItem{{{b}}}" for b in bullets])
        experience_entry = f"""\\resumeSubheading
    {{{company}}}{{{location}}}
    {{{title}}}{{{dates}}}
    \\begin{{itemize}}[leftmargin=0.2in]
{bullet_items}
    \\end{{itemize}}"""

        import re
        pattern = r"(\\section\{Experience\}[\s\S]*?\\begin\{itemize\}\[leftmargin=0\.15in, label=\{\}\])"
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            insert_pos = match.end()
            new_content = content[:insert_pos] + "\n" + experience_entry + content[insert_pos:]
            filepath.write_text(new_content, encoding="utf-8")
            return json.dumps({"success": True, "message": f"Added experience entry for {company}"})
        else:
            return json.dumps({"error": "Could not find Experience section. Make sure the resume uses the modern template format."})
    except Exception as e:
        return json.dumps({"error": f"Error adding experience: {str(e)}"})


@mcp.tool()
def add_education(
    filename: str,
    institution: str,
    degree: str,
    dates: str,
    location: str = "",
    details: list[str] = None
) -> str:
    """
    Add a new education entry to a resume (works with modern template).

    Args:
        filename: Name of the resume file
        institution: School/University name
        degree: Degree and major
        dates: Dates attended (e.g., 'Sep 2016 -- May 2020')
        location: Location - optional
        details: Additional details (GPA, honors, coursework) - optional
    """
    ensure_dirs()
    filepath = get_resumes_dir() / ensure_tex_extension(filename)

    if not filepath.exists():
        return json.dumps({"error": f"Resume '{filename}' not found"})

    try:
        content = filepath.read_text(encoding="utf-8")

        education_entry = f"""\\resumeSubheading
    {{{institution}}}{{{location}}}
    {{{degree}}}{{{dates}}}"""

        if details:
            detail_items = "\n".join([f"        \\resumeItem{{{d}}}" for d in details])
            education_entry += f"""
    \\begin{{itemize}}[leftmargin=0.2in]
{detail_items}
    \\end{{itemize}}"""

        import re
        pattern = r"(\\section\{Education\}[\s\S]*?\\begin\{itemize\}\[leftmargin=0\.15in, label=\{\}\])"
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            insert_pos = match.end()
            new_content = content[:insert_pos] + "\n" + education_entry + content[insert_pos:]
            filepath.write_text(new_content, encoding="utf-8")
            return json.dumps({"success": True, "message": f"Added education entry for {institution}"})
        else:
            return json.dumps({"error": "Could not find Education section. Make sure the resume uses the modern template format."})
    except Exception as e:
        return json.dumps({"error": f"Error adding education: {str(e)}"})


@mcp.tool()
def get_config() -> str:
    """
    Get current configuration including directories and pdflatex status.
    """
    pdflatex = find_pdflatex()
    return json.dumps({
        "resumes_directory": str(get_resumes_dir()),
        "templates_directory": str(get_templates_dir()),
        "pdflatex_installed": pdflatex is not None,
        "pdflatex_path": pdflatex,
        "env_vars": {
            "LATEX_RESUME_DIR": "Set to customize resumes directory",
            "LATEX_TEMPLATES_DIR": "Set to customize templates directory"
        }
    }, indent=2)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
