import os
import csv

id = 1
with open('datos2.csv', 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        name = row[1]
        position = row[2]
        affiliation = row[3]
        nationality = row[4]
        yearPhD = row[5]
        picture = row[7]
        os.system ("wget " + picture + " -O img/%s" % str(id))
        topics =  row[8]
        homepage = row[10]
        twitter = row[11].replace("_", "\_")
        description = row[12]
        language = row[13]
        hobbies = row[14]
        tabs = row[15]
        looking = row[16]
        hiring = row[17]
        if name != "Name":
            print r"\noindent\begin{minipage}{0.3\textwidth}"
            print r"\includegraphics[width=\linewidth]{img/" + str(id) +"}"
            print r"\end{minipage}"
            print r"\hfill"
            print r"\begin{minipage}{0.6\textwidth}\raggedright"
            #print r"\color{color1}\uppercase{\textbf{"+name+r"}} \hspace{0.2cm}\color{black}"+email+r"\\"
            print r"\color{color1}\uppercase{\textbf{"+name+r"}} \hspace{0.2cm}\color{black}"+twitter+r"\\"
            print position+r" at "+affiliation+r"\\"
            print description+r"\\"
            print r"Hobbies: " + hobbies+r"\\"
            print r"Fav. programming language: " + language+r"}} - "+tabs+r"\\"
            if looking == "Yes":
                print r"Looking for a new position\\"
            if looking == "Yes":
                print r"Hiring\\"
            print r"\end{minipage}"
            print r"\newline"
            print r"\newline"
            print r"\newline"
        id += 1
        
