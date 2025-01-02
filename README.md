# devpost-profile-exporter
A CLI tool for exporting a Devpost user's projects, featuring parallel processing and a complete content export.

## Installation
### Linux or MacOS
```bash
git clone https://github.com/tejashah88/devpost-profile-exporter.git
cd devpost-profile-exporter
python -m venv env
source env/bin/activate
```

### Windows
```bat
git clone https://github.com/tejashah88/devpost-profile-exporter.git
cd devpost-profile-exporter
python -m venv env
env\\Scripts\\activate.bat
```

## Usage

When running this tool, it'll retrieve the user profile, find all their projects,the given format,
then scrape all relevant information for each project. Then depending on the given format, it'll save
the scraped information into a JSON or TXT file.

```bash
Usage: devpost_export.py [OPTIONS] USERNAME

  This CLI tool takes a valid Devpost username and scrapes all the user's
  projects and the corresponding information. The projects will be outputted
  into a folder with all the project details in the specified format.

Options:
  --format [text|json]   The format to save the project information (text or
                         json).  [required]
  --output [output-dir]  The output folder to store all projects. By default,
                         it saves all projects to "{username}-projects/"
  --help                 Show this message and exit.
```
