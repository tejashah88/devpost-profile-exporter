# devpost-profile-exporter
A CLI tool for exporting a Devpost user's projects, featuring parallel processing and a complete content export.

## Installation (for now)
### Linux or MacOS
```bash
git clone https://github.com/tejashah88/devpost-profile-exporter.git
cd devpost-profile-exporter
python -m venv env
source env/bin/activate
pip install --editable .
```

### Windows (UNTESTED)
```bat
git clone https://github.com/tejashah88/devpost-profile-exporter.git
cd devpost-profile-exporter
python -m venv env
env\\Scripts\\activate.bat
pip install --editable .
```

## Usage

When running this tool, it'll retrieve the user profile, find all his/her's projects,the given format,
then scrape all relevant information for each project. Then depending on the given format, it'll save
the scraped information into the optionally given output folder.

```bash
python devpost_export.py <username> <format> --output-folder [folder]
```

* `<username>` - Devpost username
* `<format>` - Either 'text' or 'json'
  * `text` - Gives a human readable report of the project (won't include links for team members and hackathons).
  * `json` Stores **all** scraped information into a json file, properly indented at 4 spaces.
* `<folder>` - The output folder to store the user's project info. By default, the folder is `<username>-projects/`
