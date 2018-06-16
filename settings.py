"""
ConfBookGenerator settings.

For more information, see:
https://github.com/gregoriorobles/ConfBookGenerator
"""

# Conference long name and short name (LaTeX special chars have to be escaped)
LONG_NAME = "11\\textsuperscript{th} Seminar on Advanced Techniques \& Tools for Software Evolution"
SHORT_NAME = "SATToSE 2018"

# Conference place and dates (LaTeX special chars have to be escaped)
PLACE = "Athens, Greece"
DATES = "July 4\\textsuperscript{th}--6\\textsuperscript{th} 2018"

# Conference Twitter hashtag (LaTeX special chars have to be escaped, e.g. # -> \#)
HASHTAG = "\#sattose18"

# Front Image of the ConfBook and logo of the conference
FRONT_IMAGE = "Panepistimiou.jpg"
LOGO = "sattose.png"

# Google Spreadsheet id
SPREADSHEET_ID = "1ythM16SC_OqYfwzg96NN6DzQrZLBU_gGMmS5AvfkWtI"

################################################################################
# For vanilla ConfBook, don't touch from this point!

# Maximum participant image size (in pixels)
IMAGE_SIZE = 512, 512 

# Maximum participant description size (in number of characters)
LIMIT_DESCRIPTION = 500 

# Google Spreadsheet column names
HEADER = ['date', 'name', 'affiliation', 'position', 'presentation', 'nationality', 'graduation', 'picture', 'homepage', 'twitter', 'looking', 'hiring', 'times']

# Other
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Yearbook Generator'
GENERATED_FILE = "generated" # name of the LaTeX and PDF file created
ERRORS_FILE = "errors.txt"
