#!/usr/bin/python3

import os
import csv
from collections import namedtuple

class Creator:

    def DataIn(self):
        with open('datos.csv', 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            form = 'name position affiliation email twitter description hobbies language tabs looking hiring'
            Datos = namedtuple('Datos', form)
            dat = map(Datos._make, spamreader)
        return dat

    def DataOut (self, dat):
        id = 1
        msg = ''
        for row in dat:
    #Faltan meter todos los datos
            msg += (r"\noindent\begin{minipage}{0.3\textwidth}" + "\n" +
                #   r"\includegraphics[width=\linewidth]{img" + str(id) +".png}" + "\n" +
                   r"\includegraphics[width=\linewidth]{img1.jpg}" + "\n" +
                   r"\end{minipage}" + "\n" +
                   r"\hfill" + "\n" +
                   r"\begin{minipage}{0.6\textwidth}\raggedright" + "\n" +
                   r"\color{color1}\uppercase{\textbf{"+row.name+r"}} \hspace{0.2cm}\color{black}"+row.email+r"\\" + "\n" +
                   r"\color{color1}\uppercase{\textbf{"+row.name+r"}} \hspace{0.2cm}\color{black}"+row.twitter+r"\\" + "\n" +
                   row.position+r" at "+row.affiliation+r"\\" + "\n" +
                   row.description+r"\\" + "\n" +
                   r"Hobbies: " + row.hobbies+r"\\" + "\n" +
                   r"Fav. programming language: " + row.language+r" - "+row.tabs+r"\\" + "\n")
            if row.looking == "Yes":
                msg += r"Looking for a new position\\"
            if row.hiring == "Yes":
                msg += r"Hiring\\"
            msg += r"\end{minipage}\newline\newline\newline"
            id += 1
        return msg


if __name__ == "__main__":
    datos = Creator().DataIn()
    generated = Creator().DataOut(datos)
    print(generated)
