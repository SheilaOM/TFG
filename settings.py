"""
ConfBookGenerator settings.
"""

# Conference long name and short name
CONFERENCE_LONG = "11\\textsuperscript{th} Seminar on Advanced Techniques \& Tools for Software Evolution"
CONFERENCE_SHORT = "SATToSE 2018"

# Conference place and dates
CONFERENCE_PLACE = "Athens, Greece"
CONFERENCE_DATES = "July 4\\textsuperscript{th}--6\\textsuperscript{th} 2018"

# Front Image of the ConfBook and logo of the conference
FRONT_IMAGE = "Panepistimiou.jpg"
LOGO = "sattose.png"

# Google Spreadsheet id
SPREADSHEET_ID = "1ythM16SC_OqYfwzg96NN6DzQrZLBU_gGMmS5AvfkWtI"

################################################################################
# For vanilla ConfBook, don't touch from this point!

# Maximum participant image size 
IMAGE_SIZE = 512, 512 

# Maximum participant description size
LIMIT_DESCRIPTION = 500 

# Google Spreadsheet columns
HEADER = ['date', 'name', 'affiliation', 'position', 'presentation', 'nationality', 'graduation', 'picture', 'homepage', 'twitter', 'looking', 'hiring', 'times']

# Other
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Yearbook Generator'


