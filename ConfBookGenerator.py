#!/usr/bin/python3

from __future__ import print_function

import os
import csv
from collections import namedtuple
import urllib.request
import string

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from PIL import Image
import pycountry

import pandas as pd
import matplotlib.pyplot as plt


SPREADSHEET_ID = '1cWBAVb_pUqJlmlaxsXmajPK3601ZxToZWv6qP3wRj3g'
HEADER = ['date', 'name', 'position', 'affiliation', 'nationality', 'graduation', 'picture', 'topics', 'homepage', 'twitter', 'presentation', 'programming', 'hobbies', 'looking', 'hiring']

SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Yearbook Generator'
IMAGE_SIZE = 512, 512 # Maximum participant image size
LIMIT_DESCRIPTION = 200 # Maximum participant description size

class Creator():

    def __init__(self):
        self.fields = []        # NamedTuple with fields and their info
        self.err = open("errors.txt", "w", encoding="utf-8")  # FIXME: should be a parameter; default STDERR
                                            # FIXME: should be the path, not the file descriptor!

        try:
            import argparse
            self.flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            self.flags = None


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
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            credentials = tools.run_flow(flow, store, self.flags)
            print('Storing credentials to ' + credential_path)
        return credentials


    def spreadsheet_to_namedtuple(self):
        """
        Obtains personal data from the Google spreadsheet
        and returns a namedtuple
        """
        credentials = c.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        rangeName = 'A2:'+ string.ascii_uppercase[len(HEADER)-1] # sheet, and rows and columns
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            id = 1
            Fields = namedtuple("Fields", ' '.join(HEADER))
            for row in values:
                id += 1
                if row and len(row) == len(HEADER):  # in case of an empty row (deleted by hand from the spreadsheet)
                    fields = Fields(*row)
                    self.fields.append(fields)
                elif (len(row) < len(HEADER)) and (len(row) > (len(HEADER) - 5)):
                    while(len(row) != len(HEADER)):
                        row.append("-")
                    fields = Fields(*row)
                    self.fields.append(fields)
                else:
                    self.err.write("- Error. Not enough values in row " + str(id) + ": "+ str(row) + "\n")


    def make_chars_latex_friendly(self, row):
        """
        Makes special characters in the data LaTeX-friendly
        """
        for data, name in zip(row, row._fields):
            if (name != "picture"):
                for c in ["_", "&", "#", "$", "%", "{", "}", "^"]:
                    if data.find(c) != -1:
                        if c == '~':
                            data = data.replace(c, "\\textasciitilde ")
                        elif c == '\\':
                            data = data.replace(c, "\\textbackslash ")
                        elif c == '\n':
                            data = data.replace(c, "")
                        else:
                            data = data.replace(c, "\\" + c)
                        row = row._replace(**{name:data})
        return row


    def download_image (self, row, id):
        """
        Given the row (of data) and the id of the participants
        Downloads its image to a file (converts it to jpeg if necessary),
        and resizes it

        Returns the (relative) path to the image file
        """

        url = row.picture
        msgError = ("It's impossible to download the image automatically. Please, try download it manually, and" +
                    "name it img" + str(id) + ".jpg. Next, change the name of this person's image in the .tex")

        try:
            resp = urllib.request.urlopen(url)          # Reads URL (does not download)
        except ValueError as e:
            image = "images/img0.jpg"
            self.err.write("- Error in image of " + row.name + " (pos. " + str(id) + ") -> This person hasn't provided image link.\n")
            return image
        except:
            image = "images/img0.jpg"
            self.err.write("- Error in image of " + row.name + " (pos. " + str(id) + ") -> " + msgError + "\n")
            return image

        contentType = resp.info().get("Content-Type")
        if contentType.startswith("image/"):
            imgType = contentType.split('/')[-1]
            imgType = imgType.split(';')[0]
            nameImage = "images/img" + str(id) + "." + imgType
            urllib.request.urlretrieve(url, nameImage)  # If URL is an image, then download

            if imgType == "webp":  # If webp image, convert to jpeg
                im = Image.open(nameImage).convert("RGB")
                im.thumbnail(IMAGE_SIZE, Image.ANTIALIAS)
                im.save("images/img" + str(id) + ".jpg", "jpeg")
                os.remove(nameImage)
            else:
                im = Image.open(nameImage)
                im.thumbnail(IMAGE_SIZE, Image.ANTIALIAS)
                im = im.convert('RGB')
                im.save(nameImage, imgType)

            image = nameImage
        else:
            image = "images/img0.jpg"
            self.err.write("- Error in image of " + row.name + " (pos. " + str(id) + ") -> " + msgError + "\n")

        return image


    def get_flag (self, row, id):
        """
        Given the data (row) and participant id

        Retunrs the (relative) path to its flag image
        """
        try:
            nac = pycountry.countries.get(name=row.nationality)
            flag_icon = "flags/" + nac.alpha_2.lower() + ".png"
        except KeyError:
            self.err.write("- Error in nationality of " + row.name + " (pos. " + str(id) + ") -> Country not found or not provided.\n")
            flag_icon = ""

        return flag_icon

    def cut_presentation (self, desc):
        """
        Given a participant's description (string) desc

        Returns a version of it that is at most LIMIT_DESCRIPTION long
        """
        if '"' in desc:
            desc = desc.replace('"', "''")

        if len(desc) > LIMIT_DESCRIPTION:
            description = desc[0:LIMIT_DESCRIPTION-1]
            description = description.split(" ")[0:-1]
            description = " ".join(description) + r" \ldots"
        else:
            description = desc

        return description


    def generate_graphs (self, fields):
        """
        Generate a pie chart with the statistics of the answers
        of the indicated fields
        """
        n=1
        df = pd.DataFrame(self.fields, columns=HEADER)
        for fld in HEADER:
            if fld in fields:
                plt.figure();
                tab = pd.crosstab(index=df[fld],columns="frecuencia")
                plt.pie(tab, autopct="%1.1f%%", pctdistance=0.8, radius=1.2)
                plt.legend(labels=tab.index,bbox_to_anchor=(0.9, 1), loc="upper left")
                plt.title(fld, fontsize=15)
                plt.savefig("graph" + str(n) + ".png", bbox_inches="tight")
                n += 1

        msg = (r"\newpage" + "\n" +
               r"\begin{figure}" + "\n" +
               r"\centering" + "\n")

        for i in range(n-1):
            #msg += r"\subfigure{\includegraphics[width=0.49\textwidth]{graph" + str(i+1) + "}}" + "\n"
            msg += r"\subfigure{\includegraphics[height=6cm]{graph" + str(i+1) + "}}" + "\n"

        msg += r"\end{figure}" + "\n"

        return msg


    def generate_list (self, fields):
        """
        Only for fields with "Yes/No" answers.

        Looks in the participant list (self.fields) for who has a "Yes" in then
        indicated field.

        Returns lists with the results.
        """
        msg = ""
        for fld in fields:
            if fld[0] in HEADER:
                fld_name = fld[0]
                fld_answer = fld[1]
                print(fld_name + "--" + fld_answer)
                msg += (r"\newpage" + "\n" +
                        r"\color{color1}\uppercase{\textbf{" + fld_name + r"}}\\" + "\n" +
                        r"\color{color2}People whose answer to the question of '" +
                        fld_name + "' has been '" + fld_answer + "':" + "\n" +
                        r"\begin{multicols}{2}" + "\n" +
                        r"\begin{itemize}" + "\n")
                for row in self.fields:                  #through all the participants
                    if getattr(row, fld_name) == fld_answer:     #Participants with 'answer' in the chosen 'field'
                        msg += r"\item " + row.name + "\n"
                msg += r"\end{itemize}" + "\n" + r"\end{multicols}"
        return msg


    def order_by_name(self):
        """
        Orders participants data (self.fields) by surname
        """
        surnames = [field.name.split()[-1] for field in self.fields]
        surnames = list(set(surnames))
        surnames.sort()

        newList = []
        for surname in surnames:
            for field in self.fields:
                if field.name.split()[-1] == surname:
                    newList.append(field)

        self.fields = newList


    def namedtuple_to_latex (self):
        """
        Outputs the LaTeX data
        """
        id = 1
        c.order_by_name()
        msg = r"\section*{Participants}" + "\n"

        for row in self.fields:
            print (id)
            row = c.make_chars_latex_friendly(row)
            image = c.download_image(row, id)
            flag = c.get_flag(row, id)
            description = c.cut_presentation(row.presentation)

            im = Image.open(image)
            width, height = im.size

            # Required data
            msg += (r"\noindent\begin{minipage}{0.3\textwidth}" + "\n" +
                   r"\centering" + "\n")

            if (width/height) > 1.2:
                msg += r"\includegraphics[width=5cm]{" + image + "}" + "\n"

            else:
                msg += r"\includegraphics[height=5cm]{" + image + "}" + "\n"

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
                msg += r"\hspace{0.2cm}\textit{" + row.twitter + r"}"

            if row.hiring == "Yes":
                msg += r"\hspace{0.1cm}\includegraphics[height=0.5cm]{figs/hiring.png}" + "\n"

            if row.looking == "Yes":
                msg += r"\hspace{0.1cm}\includegraphics[height=0.4cm]{figs/jobs.png}" + "\n"

            msg += r"\\" + "\n" + row.position + " at " + row.affiliation + r"\\" + "\n"

            if description:
                msg += (r"{\footnotesize " + description + r"}\\" + "\n")

            if row.homepage:
                msg += (r"{\scriptsize " + row.homepage + r"}" + "\n")

            msg += r"\end{minipage}" + "\n"

            msg += r"\newline\newline\newline\newline" + "\n"
            id += 1

        # Stats
        #msg += c.generate_graphs(['hiring', 'looking'])

        # List of people
        print("1")
        msg += c.generate_list([['hiring', 'Yes'], ['looking', 'Yes'], ['nationality', 'Spain']])
        print("2")

        self.err.close()
        return msg


if __name__ == "__main__":
    c = Creator()
    c.spreadsheet_to_namedtuple()
    participants = c.namedtuple_to_latex()
    with open("participants.tex", "w", encoding="utf-8") as partic:
        partic.write(participants)

    try:
        with open("intro.tex", "r", encoding="utf-8") as introd:
            text = introd.read().replace("\input{participants}", participants)

        with open("ConfBook.tex", "w", encoding="utf-8") as gener:
            gener.write(text)
        try:
            os.system("xelatex ConfBook.tex")
            print("PDF has been generated --> ConfBook.pdf")
        except:
            print("Impossible to generate PDF automatically. You must compile in Latex manually")

    except FileNotFoundError:
        print("Participants section created (participants.tex). Include it in your .tex")
