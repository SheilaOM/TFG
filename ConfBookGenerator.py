#!/usr/bin/python3

from __future__ import print_function

import os
import csv
from collections import namedtuple
import urllib.request

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from PIL import Image
import pycountry

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from operator import itemgetter

#SPREADSHEET_ID = '1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI' # id of Google Spreadsheet
SPREADSHEET_ID = '1cWBAVb_pUqJlmlaxsXmajPK3601ZxToZWv6qP3wRj3g'
HEADER = ['date', 'name', 'position', 'affiliation', 'nationality', 'graduation', 'dietary', 'picture', 'topics', 'looking_for', 'homepage', 'twitter', 'presentation', 'programming', 'hobbies', 'tabs', 'looking', 'hiring']

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
            if self.flags:
                credentials = tools.run_flow(flow, store, self.flags)
            else: # Needed only for compatibility with Python 2.6   - FIXME: then the rest of the script should work for Python2
                credentials = tools.run(flow, store)
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

        rangeName = 'A2:R'
#        rangeName = 'A2:'+ string.ascii_uppercase[len(HEADER)-1] # sheet, and rows and columns
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            Fields = namedtuple("Fields", ' '.join(HEADER))
            for row in values:
                if row and len(row) == len(HEADER):  # in case of an empty row (deleted by hand from the spreadsheet)
                    fields = Fields(*row)
                    self.fields.append(fields)
                else:
                    self.err.write("- Error. Not enough values in row: " + str(row) + "\n")

    def make_chars_latex_friendly(self, row):
        """
        Makes special characters in the data LaTeX-friendly
        """
        for data, name in zip(row, row._fields):
            if (name != "picture"):
                for c in ["_", "&", "#", "$", "%", "{", "}"]:
                    if data.find(c) != -1:
                        if c == '~':
                            data = data.replace(c, "\\textasciitilde ")
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
        # FIXME: long try-excepts should be enhanced

        url = row.picture
        try:
            resp = urllib.request.urlopen(url)          # Reads URL (does not download)
            contentType = resp.info().get("Content-Type")
            if contentType.startswith("image/"):
                imgType = contentType.split('/')[-1]
                imgType = imgType.split(';')[0]
                urllib.request.urlretrieve(url, "images/img" + str(id) + "." + imgType)  # If URL is an image, then download

                if imgType == "webp":  # If webp image, convert to jpeg
                    im = Image.open("images/img" + str(id) + ".webp").convert("RGB")
                    im.thumbnail(IMAGE_SIZE, Image.ANTIALIAS)
                    im.save("images/img" + str(id) + ".jpg", "jpeg")
                    os.remove("images/img" + str(id) + ".webp")
                else:
                    im = Image.open("images/img" + str(id) + "." + imgType)
                    im.thumbnail(IMAGE_SIZE, Image.ANTIALIAS)
                    im = im.convert('RGB')
                    im.save("images/img" + str(id) + "." + imgType, imgType)

                image = "images/img" + str(id) + "." + imgType
            else:
                image = "images/img0.jpg"
                self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> Download image manually (change the name of the image in generated.tex).\n")

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            image = "images/img0.jpg"
            self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> URL not found.\n")

        except ValueError:
            image = "images/img0.jpg"
            self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> There aren't URL.\n")

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
            self.err.write("-Error in nationality of " + row.name + " (pos. " + str(id) + ") -> Country not found or not provided.\n")
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

        #if len(description) != 0:
        #    description += r"\\" + "\n"

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
        for fld in HEADER:
            if fld in fields:
                msg += (r"\newpage" + "\n" +
                        r"\color{color1}\uppercase{\textbf{" + fld + r"}}" + "\n" +
                        r"\color{color2}" + "\n" +
                        r"\begin{multicols}{2}" + "\n" +
                        r"\begin{itemize}" + "\n")
                for row in self.fields:                  #through all the participants
                    if getattr(row, fld) == "Yes":     #Participants with "Yes" in the chosen field
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

            """
            # Optional data
            opcional = False
            for fld in self.fields:
                if fld.show == "yes":
                    opcional = True
                    if fld.text != "":
                        msg += fld.text + ": " + getattr(row, fld.name) + r" - "
                    else:
                        msg += getattr(row, fld.name) + r" - "
            if opcional:
                msg = msg[:len(msg)-3]
            """

            msg += r"\end{minipage}" + "\n"

            msg += r"\newline\newline\newline\newline" + "\n"
            id += 1

        # Stats
        #msg += c.generate_graphs(['hiring', 'looking'])

        # List of people
        #msg += c.generate_list(['hiring', 'looking'])

        self.err.close()
        return msg


if __name__ == "__main__":
    c = Creator()
    c.spreadsheet_to_namedtuple()
    participants = c.namedtuple_to_latex()
    partic = open("participants.tex", "w", encoding="utf-8")
    partic.write(participants)
    partic.close()

    try:
        introd = open("intro.tex", "r", encoding="utf-8")
        text = introd.read().replace("\input{participants}", participants)
        introd.close()
        gener = open("generated.tex", "w", encoding="utf-8")     # FIXME: change to with
        gener.write(text)
        gener.close()
        try:
            os.system("xelatex generated.tex")
            print("PDF has been generated --> generated.pdf")
        except:
            print("Impossible to generate PDF automatically. You must compile in Latex manually")

    except FileNotFoundError:
        print("Participants section created. Include it in your .tex")
