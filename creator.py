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


class Creator():

    def __init__(self):
        self.values = []
        self.formato = {}

        try:
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None

        SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
        CLIENT_SECRET_FILE = 'client_secret.json'
        APPLICATION_NAME = 'Google Sheets API Python Quickstart'


    def get_credentials(self):
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
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials


    def get_datos(self, form):
        """
        Datos: https://docs.google.com/spreadsheets/d/1NtocNeyy0B2nOnz-Sw84EMRzejJIXcPm1g8E5Wk36u4/edit

        """
        credentials = c.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        spreadsheetId = '1NtocNeyy0B2nOnz-Sw84EMRzejJIXcPm1g8E5Wk36u4'      #id de la hoja de cálculo
        rangeName = 'Form Responses 1!2:43'                                      #hoja y filas y columnas
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            Data = namedtuple("Data", form)
            for row in values:
                while len(row) != 18:
                    row.append("")
                data = Data(*row)
                self.values.append(data)


    def DataIn(self):
        """
        Campos: https://docs.google.com/spreadsheets/d/1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI/edit
        """
        credentials = c.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        spreadsheetId = '1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI'      #id de la hoja de cálculo
        rangeName = 'form!A2:B'                                             #hoja y filas y columnas
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            form = ""
            for row in values:
                self.formato[row[0]] = row[1]           #Formato: diccionario[campo]=tipo --En el diccionario no se guardan por orden
                form += row[0] + " "                    #form para Namedtuple


        c.get_datos(form)


    def CorrectCharacters(self, row):               #Corrige los caracteres especiales
        for data, name in zip(row, row._fields):
            if (name != "url") & (name != "HomePage"):
                for c in ["_", "&", "#", "$", "%", "{", "}"]:
                    if data.find(c) != -1:
                        data = data.replace(c, "\\" + c)
                        row = row._replace(**{name:data})
        return row


    def DownloadImage (self, url, id):
        try:
            resp = urllib.request.urlopen(url)          #Lee la url (no descarga nada)
            contentType = resp.info().get("Content-Type")
            if contentType.startswith("image/"):
                imgType = contentType.split('/')[-1]
                urllib.request.urlretrieve(url, "images/img" + str(id) + "." + imgType)     #Si la url es de una imagen, la descarga
                if imgType == "webp":       #Si la imagen es de tipo webp lo convierte a jpg
                    im = Image.open("images/img" + str(id) + ".webp").convert("RGB")
                    im.save("images/img" + str(id) +".jpg","jpeg")
                    imgType = "jpg"
                    os.remove("images/img" + str(id) + ".webp")
                image = "images/img" + str(id) + "." + imgType
            else:
                image = "images/img0.png"

        except urllib.error.HTTPError:
            image = "images/img0.png"

        return image

    def CutDescription (self, desc):
        limDesc = 150;
        if len(desc) > limDesc:
            description = desc[0:limDesc-1]
            description = description.split(" ")[0:-1]
            description = " ".join(description) + r" \ldots"
        else:
            description = desc
        return description


    def DataOut (self):
        id = 1
        msg = ''
        for row in self.values:
            print (id)
            row = c.CorrectCharacters(row)
            image = c.DownloadImage(row.url, id)
            description = c.CutDescription(row.description)

            msg += (r"\noindent\begin{minipage}{0.3\textwidth}" + "\n" +
                   r"\centering" + "\n" +
                   r"\includegraphics[height=5cm]{" + image + "}" + "\n" +
                   r"\end{minipage}" + "\n" +
                   r"\hfill" + "\n" +
                   r"\begin{minipage}{0.6\textwidth}\raggedright" + "\n" +
                   r"\color{color1}\uppercase{\textbf{" + row.name + r"}}" + "\n" +
                   r"\color{color2}")

            #Comprueba si es un login de twitter
            if len(row.twitter.split()) == 1 and row.twitter[0] == "@":
                msg += r"\hspace{0.2cm}\textit{" + row.twitter + r"}" + "\n"

            msg += (r"\\" + row.position + " at " + row.affiliation + r"\\" + "\n" +
                   description + r"\\" + "\n" +
                   r"Hobbies: " + row.hobbies + r"\\" + "\n" +
                   r"Fav. programming language: " + row.language + r" - " + row.tabs + r"\\" + "\n")

            if row.looking == "Yes":
                msg += r"Looking for a new position\\"
            if row.hiring == "Yes":
                msg += r"Hiring\\"
            msg += r"\end{minipage}"

            if id%4 == 0:           #4 participantes por página. Si llega al 4º salta de página
                msg += r"\newpage" + "\n"
            else:
                msg += r"\newline\newline\newline\newline" + "\n"
            id += 1
        return msg


if __name__ == "__main__":
    c = Creator()
    c.DataIn()
    generated = c.DataOut()
    f = open("generated.tex", "w")
    f.write(generated)
    f.close()
