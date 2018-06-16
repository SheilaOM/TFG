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

## Examples

You can see at some examples of conferences thave have created their own Conference Yearbook using ConfBookGenerator:

* [MSR 2018 - Intl Working Conference on Mining Conferences](https://gsyc.urjc.es/~grex/2018-MSR-Confbook.pdf)
* [OSS 2018 - Intl Conference on Open Source Systems](https://gsyc.urjc.es/~grex/2018-OSS-Confbook.pdf)
* [SATToSE 2018](https://gsyc.urjc.es/~grex/2018-SATToSE-Confbook.pdf)

## License

Licensed under GNU General Public License (GPL), version 3 or later.

