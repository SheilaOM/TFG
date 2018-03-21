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




"""
URL original: https://docs.google.com/spreadsheets/d/1NtocNeyy0B2nOnz-Sw84EMRzejJIXcPm1g8E5Wk36u4/edit
Campos y datos (URL utilizada): https://docs.google.com/spreadsheets/d/1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI/edit
"""
class Creator():

    def __init__(self):
        self.values = []        #NamedTuple of data
        self.fields = []        #NamedTuple of fields and their info
        self.data = []     #data
        self.field_names = ""
        self.err = open("errores.txt", "w")


        try:
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None

        SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
        CLIENT_SECRET_FILE = 'client_secret.json'
        APPLICATION_NAME = 'Yearbook Generator'


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


    def get_datos(self):
        credentials = c.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        #spreadsheetId = '1NtocNeyy0B2nOnz-Sw84EMRzejJIXcPm1g8E5Wk36u4'      #id de la hoja de cálculo
        spreadsheetId = '1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI'      #id de la hoja de cálculo (campos)
        rangeName = 'Form Responses 1!A2:ZZZ'                               #hoja y filas y columnas
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName).execute()
        self.data_form = result.get('values', [])

        if not self.data_form:
            print('No data found.')
        else:
            Data = namedtuple("Data", self.field_names)
            for row in self.data_form:
                data = Data(*row)
                self.values.append(data)


    def DataIn(self):
        credentials = c.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        spreadsheetId = '1tX2SheuK8BFyp_bPEaFt_rs4gjRr_eXPEBnNadVdCaI'      #id de la hoja de cálculo
        rangeName = 'form!A2:Z'                                             #hoja y filas y columnas
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            Fields = namedtuple("Fields", "name text show statistics")
            for row in values:
                fields = Fields(*row)
                self.fields.append(fields)
                self.field_names += row[0] + " "                    #fields para Namedtuple de datos

        c.get_datos()


    def CorrectCharacters(self, row):               #Corrige los caracteres especiales
        for data, name in zip(row, row._fields):
            if (name != "picture") & (name != "HomePage"):
                for c in ["_", "&", "#", "$", "%", "{", "}"]:
                    if data.find(c) != -1:
                        data = data.replace(c, "\\" + c)
                        row = row._replace(**{name:data})
        return row


    def DownloadImage (self, row, id):
        url = row.picture
        try:
            resp = urllib.request.urlopen(url)          #Lee la url (no descarga nada)
            contentType = resp.info().get("Content-Type")
            if contentType.startswith("image/"):
                imgType = contentType.split('/')[-1]
                urllib.request.urlretrieve(url, "images/img" + str(id) + "." + imgType)     #Si la url es de una imagen, la descarga
                #urllib.request.urlretrieve(url, "images/img" + str(id))     #Si la url es de una imagen, la descarga

                if imgType == "webp":       #Si la imagen es de tipo webp lo convierte a jpg
                    im = Image.open("images/img" + str(id) + ".webp").convert("RGB")
                    im.save("images/img" + str(id) + ".jpg","jpeg")
                    os.remove("images/img" + str(id) + ".webp")

                image = "images/img" + str(id)
            else:
                image = "images/img0"
                self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> Download image manually (change the name of the image in generated.tex).\n")

        except urllib.error.HTTPError:
            image = "images/img0"
            self.err.write("-Error in image of " + row.name + " (pos. " + str(id) + ") -> URL not found.\n")

        return image

    def GetFlag (self, row, id):
        try:
            nac = pycountry.countries.get(name=row.nationality)
            flag_icon = "flags/" + nac.alpha_2.lower() + ".png"
        except KeyError:
            self.err.write("-Error in nationality of " + row.name + " (pos. " + str(id) + ") -> It's not a country.\n")
            flag_icon = ""

        return flag_icon

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
            image = c.DownloadImage(row, id)
            flag = c.GetFlag(row, id)
            description = c.CutDescription(row.description)

        #DATOS OBLIGATORIOS
            msg += (r"\noindent\begin{minipage}{0.3\textwidth}" + "\n" +
                   r"\centering" + "\n" +
                   r"\includegraphics[height=5cm]{" + image + "}" + "\n" +
                   r"\end{minipage}" + "\n" +
                   r"\hfill" + "\n" +
                   r"\begin{minipage}{0.6\textwidth}\raggedright" + "\n" +
                   r"\color{color1}\uppercase{\textbf{" + row.name + r"}}" + "\n" +
                   r"\color{color2}")

            if flag != "":
                msg += r"\hspace{0.2cm}\includegraphics{" + flag + "}" + "\n"

            #Comprueba si es un login de twitter
            if len(row.twitter.split()) == 1 and row.twitter[0] == "@":
                msg += r"\hspace{0.2cm}\textit{" + row.twitter + r"}" + "\n"

            msg += (r"\\" + row.position + " at " + row.affiliation + r"\\" + "\n" +
                   description + r"\\" + "\n")

        #DATOS OPCIONALES
            for fld in self.fields:
                if fld.show == "yes":
                    if fld.text != "":
                        msg += fld.text + ": " + getattr(row, fld.name) + r" - "
                    else:
                        msg += getattr(row, fld.name) + r" - "
            msg = msg[:len(msg)-3]

            msg += r"\end{minipage}"

            if id%4 == 0:           #4 participantes por página. Si llega al 4º salta de página
                msg += r"\newpage" + "\n"
            else:
                msg += r"\newline\newline\newline\newline" + "\n"
            id += 1


    # GRÁFICAS DE ESTADÍSTICAS
        n = 1

        df = pd.DataFrame(self.fields,columns=["name","text","show","statistics"])
        stats = pd.crosstab(index=df["statistics"],columns="frecuencia")
        fila = stats.loc[stats.index == "yes"]

        if not fila.empty:
            n_graph = int(fila["frecuencia"])
            data = pd.DataFrame(self.data_form, columns=self.field_names.split(" ")[:-1])
            plt.figure(figsize=(7,10))
            for fld in self.fields:
                if fld.statistics == "yes":
                    plt.subplot(n_graph, 1, n)

                    tab = pd.crosstab(index=data[fld.name],columns="frecuencia")
                    plt.pie(tab, autopct="%1.1f%%", radius=0.8)
                    plt.legend(labels=tab.index,loc='center left',bbox_to_anchor=(0.8, 0.5))
                    if fld.text != "":
                        plt.title(fld.text)
                    else:
                        plt.title(fld.name)
                    n += 1
            plt.savefig("graph.png")

            msg += (r"\begin{figure}" + "\n" +
                   r"\centering" + "\n" +
                   r"\includegraphics{graph}" + "\n" +
                   r"\end{figure}" + "\n")

        self.err.close()
        return msg


if __name__ == "__main__":
    c = Creator()
    c.DataIn()
    generated = c.DataOut()
    f = open("generated.tex", "w", encoding="utf-8")
    f.write(generated)
    f.close()
