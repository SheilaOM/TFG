#!/usr/bin/python3
"""
Conference Book Creator Software

by Gregorio Robles <grex@gsyc.urjc.es>

With ideas/help from:

Seila Oliva Muñoz
Jesús Moreno-León
"""

import os
import string
import urllib.request
from string import Template
from collections import namedtuple

import httplib2
import pycountry

from apiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage
from PIL import Image

import settings


def write_error(text):
    """
    Writes error messages to file
    """
    with open(settings.ERRORS_FILE, "a") as error_output:
        error_output.write(text)

def make_chars_latex_friendly(row):
    """
    Makes special characters in the data LaTeX-friendly
    """
    for data, name in zip(row, row._fields):
        if (name != "picture") & (name != "HomePage"):
            for char in ["_", "&", "#", "$", "%", "{", "}", "~", "\n"]:
                if data.find(char) != -1:
                    if char == '~':
                        data = data.replace(char, "\\textasciitilde ")
                    elif char == '\n':
                        data = data.replace(char, "")
                    else:
                        data = data.replace(char, "\\" + char)
                    row = row._replace(**{name: data})
    return row

def download_image(row, participant_id):
    """
    Given the row (of data) and the participant_id of the participants
    Downloads its image to a file (converts it to jpeg if necessary),
    and resizes it

    Returns the (relative) path to the image file

    FIXME: long try-excepts should be enhanced
    """
    url = row.picture
    image = "images/img0.jpg"  # default image
    if not url:
        write_error("- Warning: No image for " + row.name + " (pos. " + str(participant_id) + ") -> Image URL not provided.\n")
        return image

    try:
        resp = urllib.request.urlopen(url)    # Reads URL (does not download)
        content_type = resp.info().get("Content-Type")
        if content_type.startswith("image/"):
            img_type = content_type.split('/')[-1]
            img_type = img_type.split(';')[0]
            urllib.request.urlretrieve(url, "images/img" + str(participant_id) + "." + img_type)  # If URL is an image, then download

            if img_type == "webp":  # If webp image, convert to jpeg
                image = Image.open("images/img" + str(participant_id) + ".webp").convert("RGB")
                image.thumbnail(settings.IMAGE_SIZE, Image.ANTIALIAS)
                image.save("images/img" + str(participant_id) + ".jpg", "jpeg")
                os.remove("images/img" + str(participant_id) + ".webp")
            else:
                print("images/img" + str(participant_id) + "." + img_type)
                image = Image.open("images/img" + str(participant_id) + "." + img_type)
                image.thumbnail(settings.IMAGE_SIZE, Image.ANTIALIAS)
                image.save("images/img" + str(participant_id) + "." + img_type, img_type)

            image = "images/img" + str(participant_id) + "." + img_type
        else:
            write_error("- Error in image of " + row.name + " (pos. " + str(participant_id) + ") -> Please download image manually (and change the name of the image in generated.tex).\n")

    except (urllib.error.HTTPError, urllib.error.URLError):
        write_error("- Error in image of " + row.name + " (pos. " + str(participant_id) + ") -> Error in URL.\n")

    except ValueError:
        write_error("- Error in image of " + row.name + " (pos. " + str(participant_id) + ") -> Image URL is not valid.\n")

    return image

def get_flag(row, participant_id):
    """
    Given the data (row) and participant participant_id

    Returns the (relative) path to its flag image
    """
    flag_icon = ""
    if not row.nationality:
        write_error("- Warning in nationality of " + row.name + " (pos. " + str(participant_id) + ") -> Country not provided.\n")

    try:
        nac = pycountry.countries.get(name=row.nationality)
        flag_icon = "flags/" + nac.alpha_2.lower() + ".png"
    except KeyError:
        write_error("- Error in nationality of " + row.name + " (pos. " + str(participant_id) + ") -> Country not found.\n")

    return flag_icon

def cut_presentation(desc):
    """
    Given a participant's presentation (string) desc

    Returns a version of it that is at most settings.LIMIT_DESCRIPTION long
    """
    if '"' in desc:
        desc = desc.replace('"', "''")

    if len(desc) > settings.LIMIT_DESCRIPTION:
        description = desc[0:settings.LIMIT_DESCRIPTION-1]
        description = description.split(" ")[0:-1]
        description = " ".join(description) + r" \ldots"
    else:
        description = desc

    if len(description) != 0:
        description += r"\\" + "\n"

    return description

def generate_list(field_name, names):
    """
    Creates a list with the participants that have a given condition
    (i.e., are looking for a new position)
    """
    msg = ""

    msg += (r"\newpage" + "\n" +
            r"\color{color1}\uppercase{\textbf{" + field_name + r"}}" + "\n" +
            r"\color{color2}" + "\n" +
            r"\begin{multicols}{2}" + "\n" +
            r"\begin{itemize}" + "\n")
    for name in names:
        msg += r"  \item " + name + "\n"

    msg += r"\end{itemize}" + "\n" + r"\end{multicols}"
    return msg

class Creator():
    """
    ConfBookGenerator Creator class
    """

    def __init__(self):
        """
        """
        self.fields = []        # NamedTuple with fields and their info

        try:
            import argparse
            self.flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            self.flags = None

        open(settings.ERRORS_FILE, 'w').close()  # empty error files

    def get_credentials(self):
        """
        Returns the Google spreadsheet credentials
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'sheets.googleapis.com-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(settings.CLIENT_SECRET_FILE, settings.SCOPES)
            flow.user_agent = settings.APPLICATION_NAME
            credentials = tools.run_flow(flow, store, self.flags)
            print('Storing credentials to ' + credential_path)
        return credentials

    def spreadsheet_to_namedtuple(self):
        """
        Obtains personal data from the Google spreadsheet
        and returns a namedtuple in self.fields
        """
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                         'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discovery_url)

        range_name = 'A2:' + string.ascii_uppercase[len(settings.HEADER)-1]  # sheet, and rows and columns
        result = service.spreadsheets().values().get(
            spreadsheetId=settings.SPREADSHEET_ID, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            fields = namedtuple("Fields", ' '.join(settings.HEADER))
            for row in values:
                if row and len(row) == len(settings.HEADER):  # in case of an empty row (deleted by hand from the spreadsheet)
                    self.fields.append(fields(*row))
                else:
                    write_error("- Error. Not enough values in row: " + str(row) + "\n")


#    def generate_graphs(self):
#        """
#        FIXME: include docstring
#        """
#        df = pd.DataFrame(self.fields, columns=["name", "text", "show", "statistics"])
#        stats = pd.crosstab(index=df["statistics"], columns="frecuencia")
#        fila = stats.loc[stats.index == "yes"]
#
#        msg = ""
#        n = 1
#        if not fila.empty:
#            n_graph = int(fila["frecuencia"])
#            data = pd.DataFrame(self.data_form, columns=self.field_names.split(" ")[:-1])
#            for fld in self.fields:
#                if fld.statistics == "yes":
#                    plt.figure()
#                    tab = pd.crosstab(index=data[fld.name], columns="frecuencia")
#                    plt.pie(tab, autopct="%1.1f%%", pctdistance=0.8, radius=1.2)
#                    plt.legend(labels=tab.index, bbox_to_anchor=(0.9, 1), loc="upper left")
#                    if fld.text != "":
#                        plt.title(fld.text, fontsize=15)
#                    else:
#                        plt.title(fld.name, fontsize=15)
#
#                    plt.savefig("graph" + str(n) + ".png", bbox_inches="tight")
#                    n += 1
#
#            msg += (r"\newpage" + "\n" +
#                    r"\begin{figure}" + "\n" +
#                    r"\centering" + "\n")
#
#            for i in range(n-1):
#                # msg += r"\subfigure{\includegraphics[width=0.49\textwidth]{graph" + str(i+1) + "}}" + "\n"
#                msg += r"\subfigure{\includegraphics[height=6cm]{graph" + str(i+1) + "}}" + "\n"
#
#            msg += r"\end{figure}" + "\n"
#
#        return msg

    def order_by_name(self):
        """
        Orders participants data (self.fields) by surname
        """
        surnames = [field.name.split()[-1] for field in self.fields]
        surnames = list(set(surnames))
        surnames.sort()

        new_list = []
        for surname in surnames:
            for field in self.fields:
                if field.name.split()[-1] == surname:
                    new_list.append(field)

        self.fields = new_list

    def namedtuple_to_latex(self):
        """
        Outputs the LaTeX data
        """
        looking_list = []
        hiring_list = []
        participant_id = 1
        msg = r"\section*{Participants}" + "\n"

        self.order_by_name()

        for row in self.fields:
            print(participant_id)
            print(row)
            row = make_chars_latex_friendly(row)
            image_name = download_image(row, participant_id)
            flag = get_flag(row, participant_id)
            presentation = cut_presentation(row.presentation)

            image = Image.open(image_name)
            width, height = image.size

            # Required data
            msg += (r"\noindent\begin{minipage}{0.3\textwidth}" + "\n" +
                    r"\centering" + "\n")

            if (width/height) > 1.2:
                msg += r"\includegraphics[width=5cm]{" + image_name + "}" + "\n"

            else:
                msg += r"\includegraphics[height=5cm]{" + image_name + "}" + "\n"

            msg += (r"\end{minipage}" + "\n" +
                    r"\hfill" + "\n" +
                    r"\begin{minipage}{0.6\textwidth}\raggedright" + "\n" +
                    r"\color{color1}\uppercase{\textbf{" + row.name + r"}}" + "\n" +
                    r"\color{color2}")

            if flag:
                msg += r"\hspace{0.2cm}\includegraphics{" + flag + "}" + "\n"

            if row.graduation:
                msg += (r"\hspace{0.1cm}{\scriptsize (PhD " + row.graduation + ")}\n")

            # Checks if it is a Twitter handle
            if len(row.twitter.split()) == 1 and row.twitter[0] == "@":
                msg += r"\hspace{0.2cm}\textit{" + row.twitter + r"}" + "\n"

            if row.hiring == "Yes":
                msg += r"\hspace{0.1cm}\includegraphics[height=0.5cm]{figs/hiring.png}" + "\n"

            if row.looking == "Yes":
                msg += r"\hspace{0.1cm}\includegraphics[height=0.4cm]{figs/jobs.png}" + "\n"

            msg += (r"\\" + "\n" + row.position + " at " + row.affiliation + r"\\" + "\n")
            if presentation:
                msg += (r"{\footnotesize " + presentation + "}")
            if row.homepage:
                msg += (r"{\scriptsize " + row.homepage + "}\n")

            if row.looking == "Yes":
                looking_list.append(row.name)

            if row.hiring == "Yes":
                hiring_list.append(row.name)

            msg += "\n" + r"\end{minipage}" + "\n"

            if participant_id % 4 == 0:  # 4 participants per page. After fourth, new page
                msg += r"\newpage" + "\n"
            else:
                msg += r"\newline\newline\newline\newline" + "\n"
            participant_id += 1

# If you want to have the "Looking for a position" and "My lab is hiring" listed explicitly
#        msg += generate_list('Looking for a position', looking_list)
#        msg += generate_list('My lab is hiring', hiring_list)

        # Stats
#        msg += self.generate_graphs()

        return msg


if __name__ == "__main__":
    # Creating front page
    s = Template(open('tex/defs2.tpl').read())
    tex_header = s.safe_substitute(conference_long=settings.LONG_NAME, conference_short=settings.SHORT_NAME, conference_place=settings.PLACE, conference_dates=settings.DATES, conference_hashtag=settings.HASHTAG, conference_frontimage=settings.FRONTIMAGE, conference_logo=settings.LOGO, frontimage_width=settings.FRONTIMAGE_WIDTH, logo_height=settings.LOGO_HEIGHT)

    # Inserting participants
    creator = Creator()
    creator.spreadsheet_to_namedtuple()
    participants_tex = creator.namedtuple_to_latex()
    with open(settings.GENERATED_FILE + ".tex", "w", encoding="utf-8") as generated_file:
        try:
            introd = open("tex/intro.tex", "r", encoding="utf-8")
            content = introd.read().replace("\input{defs2}", tex_header).replace("\input{participants}", participants_tex)
            introd.close()
            generated_file.write(content)
        except FileNotFoundError:
            generated_file.write(participants_tex)
            print("Participants section created. Include it in your .tex")

    # Compiling to get PDF
    try:
        os.system("xelatex " + settings.GENERATED_FILE + ".tex")
        print("PDF has been generated --> " + settings.GENERATED_FILE + ".pdf")
    except:
        print("Impossible to generate PDF automatically. You must compile in LaTeX manually")
