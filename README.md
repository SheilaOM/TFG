# ConfBookGenerator

ConfBookGenerator is a tool to create Conference Books with information from participants.

Conference participants fill out a Google Form. The data is stored in a Google Spreadsheet. ConfBookGenerator takes the data from the Google Spreadsheet and generates a LaTeX file that is compiled into a PDF.

## Usage

```
usage: python3 creator.py

```

## Requirements

* Python >= 3
* google-api-python-client >= 1.6.5
* pycountry >= 18.2.23
* Pillow>=5.1.0
* oauth2client>=4.1.2
* latex-xetex >= 3
