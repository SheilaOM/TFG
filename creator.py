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


    def DataIn(self):
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
                self.formato[row[0]] = row[1]
                form += row[0] + " "

            print(self.formato)


    #    form = 'name position affiliation email twitter url description hobbies language tabs looking hiring'
        with open('datos.csv', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            Data = namedtuple("Data", form)
            for row in reader:
                data = Data(*row)
                self.values.append(data)


    def DataOut (self):
        id = 1
        msg = ''
        for row in self.values:
            urllib.request.urlretrieve(row.url, "img" + str(id) + ".jpg")

            msg += (r"\noindent\begin{minipage}{0.3\textwidth}" + "\n" +
                   r"\includegraphics[width=\linewidth]{img" + str(id) + ".jpg}" + "\n" +
                   r"\end{minipage}" + "\n" +
                   r"\hfill" + "\n" +
                   r"\begin{minipage}{0.6\textwidth}\raggedright" + "\n" +
                   r"\color{color1}\uppercase{\textbf{"+row.name+r"}}\\" + "\n" +
                   r"\color{color2}\textit{" + row.email + "}\hspace{0.2cm}" +
                   r"\color{color2}\textit{" + row.twitter + r"}\\" + "\n" +
                   row.position + " at " + row.affiliation + r"\\" + "\n" +
                   row.description + r"\\" + "\n" +
                   r"Hobbies: " + row.hobbies + r"\\" + "\n" +
                   r"Fav. programming language: " + row.language + r" - " + row.tabs + r"\\" + "\n")
            if row.looking == "Yes":
                msg += r"Looking for a new position\\"
            if row.hiring == "Yes":
                msg += r"Hiring\\"
            msg += r"\end{minipage}\newline\newline\newline"
            id += 1
        return msg


if __name__ == "__main__":
    c = Creator()
    c.DataIn()
    generated = c.DataOut()
    f = open("generated.tex", "w")
    f.write(generated)
    f.close()
