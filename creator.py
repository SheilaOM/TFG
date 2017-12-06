#!/usr/bin/python3

import os
import csv
from collections import namedtuple
import urllib.request

class Creator():

    def __init__(self):
        self.values = []

    def DataIn(self):
        form = 'name position affiliation email twitter url description hobbies language tabs looking hiring'

        with open('datos.csv', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            Data = namedtuple("Data", form)
            for row in reader:
                data = Data(*row)
                self.values.append(data)
        #print(self.values)

    def DataOut (self):
        id = 1
        msg = ''
        #print(self.values)
        for row in self.values:
            urllib.request.urlretrieve(row.url, "img" + str(id) + ".jpg")
    #Faltan meter todos los datos
        #    print("adios", row)
            msg += (r"\noindent\begin{minipage}{0.3\textwidth}" + "\n" +
                #   r"\includegraphics[width=\linewidth]{img" + str(id) +".png}" + "\n" +
                   r"\includegraphics[width=\linewidth]{img" + str(id) + ".jpg}" + "\n" +
                   r"\end{minipage}" + "\n" +
                   r"\hfill" + "\n" +
                   r"\begin{minipage}{0.6\textwidth}\raggedright" + "\n" +
                   r"\color{color1}\uppercase{\textbf{"+row.name+r"}}\\" + "\n" +
                   r"\color{color2}\textit{" + row.email + "}\hspace{0.2cm}" +
                   r"\color{color2}\textit{" + row.twitter + r"}\\" + "\n" + row.position +
                   r" at " + row.affiliation + r"\\" + "\n" +
                   row.description+r"\\" + "\n" +
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
