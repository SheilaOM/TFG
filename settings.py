"""
ConfBookGenerator settings.
"""
# Google Spreadsheet id
SPREADSHEET_ID = "1cWBAVb_pUqJlmlaxsXmajPK3601ZxToZWv6qP3wRj3g"

# Conference long name and short name (LaTeX special chars have to be escaped)
LONG_NAME = "15\\textsuperscript{th} International Conference on Mining Software Repositories"
SHORT_NAME = "MSR 2018"

# Conference place and dates (LaTeX special chars have to be escaped)
PLACE = "Gothenburg, Sweden"
DATES = "Mat 28\\textsuperscript{th}--29\\textsuperscript{th} 2018"

# Front Image of the ConfBook and logo of the conference (and sizes)
FRONT_IMAGE = "cover.png"
LOGO = "logo.png"
FRONT_IMAGE_WIDTH = "14cm"
LOGO_HEIGHT = "1cm"

# Google Spreadsheet column names
HEADER = ['date', 'name', 'position', 'affiliation', 'nationality', 'graduation', 'picture', 'topics', 'homepage', 'twitter', 'presentation', 'programming', 'hobbies', 'looking', 'hiring']
