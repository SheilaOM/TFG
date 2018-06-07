#!/usr/bin/python3
"""
Conference Book Creator Software

by Gregorio Robles <grex@gsyc.urjc.es>

With ideas/help from:

Seila Oliva Muñoz
Jesús Moreno-León
"""

from __future__ import print_function

import os
import csv
import string
from collections import namedtuple
import urllib.request
from PIL import Image
import pycountry

import httplib2
from apiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SPREADSHEET_ID = '1-FMbSRGHMeYn9T0k5jLOsyh9CyAslc2OUrCj9ewaqT0'  # id of Google Spreadsheet
HEADER = ['date', 'name', 'affiliation', 'position', 'presentation', 'nationality', 'graduation', 'picture', 'homepage', 'twitter', 'looking', 'hiring']

SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Yearbook Generator'
IMAGE_SIZE = 512, 512 # Maximum participant image size 
LIMIT_DESCRIPTION = 500 # Maximum participant description size


class Creator():
    """
    """

    def __init__(self):
        """
        """
        self.fields = []        # NamedTuple with fields and their info
        self.err = open("errors.txt", "w") # FIXME: should be a parameter; default STDERR
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
            else: # Needed only for compatibility with Python 2.6 - FIXME: then the rest of the script should work for Python2
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def spreadsheet_to_namedtuple(self):
        """
        Obtains personal data from the Google spreadsheet
        and returns a namedtuple in self.fields  
        """
        credentials = c.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        rangeName = 'A2:'+ string.ascii_uppercase[len(HEADER)-1]  # sheet, and rows and columns
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
                    self.err.write("- Error. Not enough vaalues in row: " + str(row) + "\n")


    def make_chars_latex_friendly(self, row):
        """
        Makes special characters in the data LaTeX-friendly
        """
        for data, name in zip(row, row._fields):
            if (name != "picture") & (name != "HomePage"):
                for c in ["_", "&", "#", "$", "%", "{", "}", "~", "\n"]:
                    if data.find(c) != -1:
                        if c == '~':
                            data = data.replace(c, "\\textasciitilde ")
                        elif c == '\n':
                            data = data.replace(c, "")
                        else:
                            data = data.replace(c, "\\" + c)
                        row = row._replace(**{name:data})
        return row


    def download_image(self, row, id):
        """
        Given the row (of data) and the id of the participants
        Downloads its image to a file (converts it to jpeg if necessary),
        and resizes it
        
        Returns the (relative) path to the image file
        
        FIXME: long try-excepts should be enhanced
        """
        url = row.picture
        image = "images/img0.jpg" # default image
        if not url:
            self.err.write("- Warning: No image for " + row.name + " (pos. " + str(id) + ") -> Image URL not provided.\n")
            return image
            
        try:
            resp = urllib.request.urlopen(url)    # Reads URL (does not download)
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
                    print("images/img" + str(id) + "." + imgType)
                    im = Image.open("images/img" + str(id) + "." + imgType)
                    im.thumbnail(IMAGE_SIZE, Image.ANTIALIAS)
                    im.save("images/img" + str(id) + "." + imgType, imgType)

                image = "images/img" + str(id) + "." + imgType
            else:
                self.err.write("- Error in image of " + row.name + " (pos. " + str(id) + ") -> Please download image manually (and change the name of the image in generated.tex).\n")

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            self.err.write("- Error in image of " + row.name + " (pos. " + str(id) + ") -> Error in URL.\n")

        except ValueError:
            self.err.write("- Error in image of " + row.name + " (pos. " + str(id) + ") -> Image URL is not valid.\n")

        return image


    def get_flag(self, row, id):
        """
        Given the data (row) and participant id
        
        Retunrs the (relative) path to its flag image
        """
        flag_icon = ""
        if not row.nationality:
            self.err.write("- Warning in nationality of " + row.name + " (pos. " + str(id) + ") -> Country not provided.\n")

        try:
            nac = pycountry.countries.get(name=row.nationality)
            flag_icon = "flags/" + nac.alpha_2.lower() + ".png"
        except KeyError:
            self.err.write("- Error in nationality of " + row.name + " (pos. " + str(id) + ") -> Country not found.\n")

        return flag_icon

    def cut_presentation(self, desc):
        """
        Given a participant's presentation (string) desc
        
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

        if len(description) != 0:
            description += r"\\" + "\n"

        return description


    def generate_graphs(self):
        """
        FIXME: include docstring
        """
        df = pd.DataFrame(self.fields,columns=["name", "text", "show", "statistics"])
        stats = pd.crosstab(index=df["statistics"], columns="frecuencia")
        fila = stats.loc[stats.index == "yes"]

        msg = ""
        n = 1
        if not fila.empty:
            n_graph = int(fila["frecuencia"])
            data = pd.DataFrame(self.data_form, columns=self.field_names.split(" ")[:-1])
            for fld in self.fields:
                if fld.statistics == "yes":
                    plt.figure();
                    tab = pd.crosstab(index=data[fld.name],columns="frecuencia")
                    plt.pie(tab, autopct="%1.1f%%", pctdistance=0.8, radius=1.2)
                    plt.legend(labels=tab.index,bbox_to_anchor=(0.9, 1), loc="upper left")
                    if fld.text != "":
                        plt.title(fld.text, fontsize=15)
                    else:
                        plt.title(fld.name, fontsize=15)

                    plt.savefig("graph" + str(n) + ".png", bbox_inches="tight")
                    n += 1

            msg += (r"\newpage" + "\n" +
                    r"\begin{figure}" + "\n" +
                    r"\centering" + "\n")

            for i in range(n-1):
                #msg += r"\subfigure{\includegraphics[width=0.49\textwidth]{graph" + str(i+1) + "}}" + "\n"
                msg += r"\subfigure{\includegraphics[height=6cm]{graph" + str(i+1) + "}}" + "\n"

            msg += r"\end{figure}" + "\n"

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

    def generate_list(self, field_name, names):
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

    def namedtuple_to_latex(self):
        """
        Outputs the LaTeX data
        """
        lookingList = []
        hiringList = []
        id = 1
        msg = r"\section*{Participants}" + "\n"
        
        self.order_by_name()

        for row in self.fields:
            print(id)
            print(row)
            row = c.make_chars_latex_friendly(row)
            image = c.download_image(row, id)
            flag = c.get_flag(row, id)
            presentation = c.cut_presentation(row.presentation)

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
                lookingList.append(row.name)
                
            if row.hiring ==  "Yes":
                hiringList.append(row.name)
                
            msg += "\n" + r"\end{minipage}" + "\n"

            if id%4 == 0:   # 4 participants per page. After fourth, new page
                msg += r"\newpage" + "\n"
            else:
                msg += r"\newline\newline\newline\newline" + "\n"
            id += 1

       # If you want to have the "Looking for a position" and "My lab is hiring" listed explicitly
#        msg += self.generate_list('Looking for a position', lookingList)
#        msg += self.generate_list('My lab is hiring', hiringList)

        # Stats
#        msg += c.generate_graphs()

        self.err.close()
        return msg


if __name__ == "__main__":
    c = Creator()
    c.spreadsheet_to_namedtuple()
    generated = c.namedtuple_to_latex()
    gener = open("generated.tex", "w", encoding="utf-8") # FIXME: change to with

    try:
        introd = open("intro.tex", "r", encoding="utf-8")
        text = introd.read().replace("\input{participants}", generated)
        introd.close()
        gener.write(text)
    except FileNotFoundError:
        gener.write(generated)
        print("Participants section created. Include it in your .tex")
    gener.close()

    try:
        os.system("xelatex generated.tex")
        print("PDF has been generated --> generated.pdf")
    except:
        print("Impossible to generate PDF automatically. You must compile in Latex manually")

