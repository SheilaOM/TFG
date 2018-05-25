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


SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Yearbook Generator'


IMAGE_SIZE = 512, 512 # Maximum participant image size 
LIMIT_DESCRIPTION = 250 # Maximum participant description size
SPREADSHEET_ID = '1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI' # id of Google Spreadsheet

"""
Original URL: https://docs.google.com/spreadsheets/d/1NtocNeyy0B2nOnz-Sw84EMRzejJIXcPm1g8E5Wk36u4/edit
Fields and data (used URL): https://docs.google.com/spreadsheets/d/1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI/edit
"""


class Creator():
    """
    """

    def __init__(self):
        """
        """
        self.values = []       # NamedTuple with data
        self.fields = []        # NamedTuple with fields and their info
        self.data = []     # data
        self.field_names = ""
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

    def get_datos(self):
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

        #rangeName = 'Form Responses 1!A2:ZZZ'   # sheet, and rows and columns
        rangeName = 'MSR!A2:ZZZ'                # sheet, and rows and columns - FIXME! Belongs to configuration
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=rangeName).execute()
        self.data_form = result.get('values', [])

        if not self.data_form:
            print('No data found.')
        else:
            Data = namedtuple("Data", self.field_names)
            for row in self.data_form:
                data = Data(*row)
                self.values.append(data)

    #
    def DataIn(self):
        """
        
        """
        credentials = c.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        rangeName = 'form!A2:Z'         # sheet, and rows and columns - FIXME! belongs to configuration
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            Fields = namedtuple("Fields", "name text show statistics")
            for row in values:
                fields = Fields(*row)
                self.fields.append(fields)
                self.field_names += row[0] + " "  # fields for Namedtuple with data

        c.get_datos()


    def CorrectCharacters(self, row):
        """
        Makes special characters in the data LaTeX-friendly
        """
        for data, name in zip(row, row._fields):
            if (name != "picture") & (name != "HomePage"):
                for c in ["_", "&", "#", "$", "%", "{", "}"]:
                    if data.find(c) != -1:
                        data = data.replace(c, "\\" + c)
                        row = row._replace(**{name:data})
        return row


    def DownloadImage (self, row, id):
        """
        Given the row (of data) and the id of the participants
        Downloads its image to a file (converts it to jpeg if necessary),
        and resizes it
        
        Returns the (relative) path to the image file
        
        FIXME: long try-excepts should be enhanced
        """
        url = row.picture
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
                image = "images/img0.jpg"
                self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> Download image manually (change the name of the image in generated.tex).\n")

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            image = "images/img0.jpg"
            self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> URL not found.\n")

        except ValueError:
            image = "images/img0.jpg"
            self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> There aren't URL.\n")

        return image


    def GetFlag (self, row, id):
        """
        Given the data (row) and participant id
        
        Retunrs the (relative) path to its flag image
        """
        try:
            nac = pycountry.countries.get(name=row.nationality)
            flag_icon = "flags/" + nac.alpha_2.lower() + ".png"
        except KeyError:
            self.err.write("-Error in nationality of " + row.name + " (pos. " + str(id) + ") -> It's not a country.\n")
            flag_icon = ""

        return flag_icon

    def CutDescription (self, desc):
        """
        Given a participant's description (string) desc
        
        Returns a version of it that is at most LIMIT_DESCRIPTION long
        """
        limDesc = LIMIT_DESCRIPTION;
        if len(desc) > limDesc:
            description = desc[0:limDesc-1]
            description = description.split(" ")[0:-1]
            description = " ".join(description) + r" \ldots"
        else:
            description = desc

        if len(description) != 0:
            description += r"\\" + "\n"

        return description


    def GenerateGraphics (self):
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
        Orders participants (self.values) by family name
        
        TODO
        """
        pass
        
    def looking_and_searching(self):
        """
        Looks in the participant list (self.values) for who is looking for a
        new position or searching for applicants
        
        Returns two lists (looking, searching) 
        (and removes that data from self.values)
        
        TODO
        """
        pass

    def DataOut (self):
        """
        Outputs the LaTeX data
        """
        id = 1
        msg = r"\section*{Participants}" + "\n"
        
        order_by_name()
        lookingList, searchingList = looking_and_searching()

        for row in self.values:
            print (id)
            row = c.CorrectCharacters(row)
            image = c.DownloadImage(row, id)
            flag = c.GetFlag(row, id)
            description = c.CutDescription(row.description)

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

            if flag != "":
                msg += r"\hspace{0.2cm}\includegraphics{" + flag + "}" + "\n"

            # Checks if it is a Twitter handle
            if len(row.twitter.split()) == 1 and row.twitter[0] == "@":
                msg += r"\hspace{0.2cm}\textit{" + row.twitter + r"}"

            msg += (r"\\" + "\n" + row.position + " at " + row.affiliation + r"\\" + "\n" +
                   description)

            # Optional data
            for fld in self.fields:
                if fld.show == "yes":
                    if fld.text != "":
                        msg += fld.text + ": " + getattr(row, fld.name) + r" - "
                    else:
                        msg += getattr(row, fld.name) + r" - "
            msg = msg[:len(msg)-3]

            msg += "\n" + r"\end{minipage}" + "\n"

            if id%4 == 0:   # 4 participants per page. After fourth, new page
                msg += r"\newpage" + "\n"
            else:
                msg += r"\newline\newline\newline\newline" + "\n"
            id += 1

        # Stats
        msg += c.GenerateGraphics()

        self.err.close()
        return msg


if __name__ == "__main__":
    c = Creator()
    c.DataIn()
    generated = c.DataOut()
    gener = open("generated.tex", "w", encoding="utf-8") # FIXME: change to with

    try:
        introd = open("intro.tex", "r", encoding="utf-8")
        text = introd.read().replace("\input{participants}", generated)
        introd.close()
        gener.write(text)
        try:
            os.system("xelatex generated.tex")
            print("PDF has been generated --> generated.pdf")
        except:
            print("Impossible to generate PDF automatically. You must compile in Latex manually")

    except FileNotFoundError:
        gener.write(generated)
        print("Participants section created. Include it in your .tex")

    gener.close()
