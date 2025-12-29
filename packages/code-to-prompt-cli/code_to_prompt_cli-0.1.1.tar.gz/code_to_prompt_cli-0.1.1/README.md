# code-to-prompt

Pack an entire codebase into a single, clean, LLM-ready text prompt.

`code-to-prompt` recursively reads a folder (typically a repository), filters out noise
(binaries, build artifacts, dependencies), and outputs a single text file formatted
for direct copy-paste into LLMs like ChatGPT, Claude, Cursor, or GitHub Copilot Chat.

No AI, no network calls — pure local filesystem processing.



## Installation

Using pipx (recommended for CLI tools):

```bash
pipx install code-to-prompt-cli
```

Or with pip:

```bash
pip install code-to-prompt-cli
```



## Usage

```bash
# Basic usage (outputs <folder_name>_output.txt)
code_to_prompt ./my-project

# Custom output file
code_to_prompt ./my-project output.txt

# Skip specific files by name
code_to_prompt ./my-project --skip config.py secrets.json
```

The output file contains:

* Relative file paths
* Fenced code blocks
* Clean, deterministic ordering

This format is optimized for pasting directly into LLM prompts.



## How It Works

### Visual overview

````text
┌────────────────────────────────────────────────┐
│                Codebase / Folder               │
│                                                │
│  src/                                          │
│   ├─ main.py                                   │
│   ├─ utils.py                                  │
│   ├─ __pycache__/        (ignored)             │
│   │    └─ utils.cpython-312.pyc                │
│   ├─ config.yaml                               │
│   └─ api/                                      │
│       └─ handlers.py                           │
│                                                │
│  .git/                   (ignored)             │
│  .gitignore              (ignored)             │
│  node_modules/           (ignored)             │
│                                                │
└────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────┐
│                code-to-prompt                  │
│                                                │
│  • Walk folders                                │
│  • Skip noise                                  │
│  • Read code files                             │
│                                                │
└────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────┐
│              Single text output                │
│                                                │
│  src/main.py                                   │
│  ```                                           │
│  ...                                           │
│  ```                                           │
│                                                │
│  src/utils.py                                  │
│  ```                                           │
│  ...                                           │
│  ```                                           │
│                                                │
│  src/config.yaml                               │
│  ```                                           │
│  ...                                           │
│  ```                                           │
│                                                │
│  api/handlers.py                               │
│  ```                                           │
│  ...                                           │
│  ```                                           │
│                                                │
└────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────┐
│                 Paste into LLM                 │
│      (ChatGPT / Claude / Cursor / Copilot)     │
└────────────────────────────────────────────────┘
````

---

## What This Is For

* Sharing an entire codebase with an LLM for review or debugging
* Asking architectural or design questions about a repository
* Providing full project context to AI coding assistants
* Creating reproducible, structured prompts instead of ad-hoc copy-paste



## Features

* Recursive folder traversal
* Intelligent filtering of non-code and binary files
* Skips common directories (`.git`, `node_modules`, `__pycache__`, etc.)
* Supports many file types:
  Python, JavaScript/TypeScript, HTML/CSS, JSON, YAML, Markdown, Shell, SQL, and more
* Output formatted for LLM consumption (paths + fenced blocks)
* No external dependencies



## License

MIT
