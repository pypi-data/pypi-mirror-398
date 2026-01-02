# :notebook: notes_md

A lightweight CLI for managing Markdown notes per project, backed by Git.

Each directory you work in gets its own notes folder, stored in a centralized
location(`$HOME/notes` by default) and synced with Git. Notes are opened in your `$EDITOR` and designed to
stay out of your working directory.

## Installation
### PyPI
```bash
pip install notes_md
```

### Development
```bash
git clone https://github.com/viacoffee/notes_md.git
cd notes_md
pip install -e .
```

## Quick Start
```bash
notes_md init
notes_md add my_awesome_notes
notes_md sync
```

## Configuration
On first run, `notes_md` creates a config file in your home directory:
```yaml
# $HOME/.config/notes_md/config.yaml

notes_dir: ~/notes
```
This directory will contain one subdirectory per _project_. _Projects_ are created on `notes_md init` and use the current working directory as the project name.

### Editor
notes_md uses `$EDITOR` (falls back to `nano`)

### Git
For syncing, the `$HOME/notes` directory should be a git repo. `notes_md sync` triggers a commit and push to that repo.

## Commands
| Command            | Description                                                    |
| ------------------ | -------------------------------------------------------------- |
| `init`             | Initialize a notes directory for the current working directory |
| `add NOTE_NAME`    | Create a new note, and opens it in `$EDITOR`                   |
| `list`             | List notes for the current project and select one to open      |
| `open NOTE_NAME`   | Open a note in `$EDITOR`                                       |
| `remove NOTE_NAME` | Remove a note using (triggers `git rm`)                        |
| `sync`             | Commit and push notes (only if changes exist)                  |
| `books`            | List all notebooks and open one in `$EDITOR`                   |

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
