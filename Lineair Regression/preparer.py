#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Ici, on va utiliser des outils existants
# Et programmer le reste (ce qu'on a pas pu trouver dans ces outils)
# Le but est de se familiariser avec ces outils

import pandas
import sqlite3
import numpy
from lxml import etree

###############################
### II-6-1 Lecture des données
###############################

#lire le premier fichier (CSV)
adult1 = pandas.read_csv("../../data/adult1.csv", skipinitialspace=True)

#lire le deuxième fichier (CSV)
#     - séparateur (;)
#     - pas d'entête (la première ligne contient des données)
noms = ["class", "age", "sex", "workclass", "education", "hours-per-week", "marital-status"]
adult2 = pandas.read_csv("../../data/adult2.csv", skipinitialspace=True, sep=";", header=None, names=noms)

#lire les données à partir d'un fichier Sqlite
#Les ? doivent être Considérées comme des NaN
con = sqlite3.connect("../../data/adult3.db")
adult3 = pandas.read_sql_query("SELECT * FROM income", con)
adult3 = adult3.replace("?", numpy.nan)

#valider le fichier XML
parser = etree.XMLParser(dtd_validation=True)
arbre = etree.parse("../../data/adult4.xml", parser)

def valeur_noeud(noeud):
    return noeud.text if noeud is not None else numpy.nan

noms2 = ["id", "age", "workclass", "education", "marital-status", "sex", "hours-per-week", "class"]
adult4 = pandas.DataFrame(columns=noms2)

for candidat in arbre.getroot():
    idi = candidat.get("id")
    age = valeur_noeud(candidat.find("age"))
    workclass = valeur_noeud(candidat.find("workclass"))
    education = valeur_noeud(candidat.find("education"))
    marital = valeur_noeud(candidat.find("marital-status"))
    sex = valeur_noeud(candidat.find("sex"))
    hours = valeur_noeud(candidat.find("hours-per-week"))
    klass = valeur_noeud(candidat.find("class"))

    adult4 = adult4.append(
        pandas.Series([idi, age, workclass, education, marital, sex, hours, klass],
        index=noms2), ignore_index=True)

####################################
### II-6-2 Intégration des données
####################################

#### Ordre et noms différents des caractéristiques
#### ----------------------------------------------

# Renommer les caractéristiques
adult3.rename(columns={"num": "id", "hours-per-day": "hours-per-week"}, inplace=True)
adult1.rename(columns={"Hours-per-week": "hours-per-week", "Marital-status": "marital-status"}, inplace=True)

# Ordonner les caractéristiques
ordre = ["age", "workclass", "education", "marital-status", "sex", "hours-per-week", "class"]
adult1 = adult1.reindex(ordre + ["occupation"], axis=1)
adult2 = adult2.reindex(ordre, axis=1)
adult3 = adult3.reindex(ordre + ["id"], axis=1)
adult4 = adult4.reindex(ordre + ["id"], axis=1)

#### Problème d'échelle
#### --------------------

#transformer les heurs/jour à heurs/semaine
adult3["hours-per-week"] *= 5

#### Echantillons (enregistrement) redondants
#### ----------------------------------------

# concaténer les enregistrements des deux tables
adult34 = pandas.concat([adult3, adult4], ignore_index=True)
# définir le type de "id" comme étant entier, et remplacer la colonne
adult34["id"] = pandas.to_numeric(adult34["id"], downcast="integer")
# ordonner les enregistrements par "id"
adult34 = adult34.sort_values(by="id")
# regrouper les par "id", et pour chaque groupe remplacer les
# valeurs absentes par une valeur précédente dans le même groupe
adult34 = adult34.groupby("id", as_index=False).ffill()
# supprimer les enregistrements dupliqués
# on garde les derniers, puisqu'ils sont été réglés
adult34.drop_duplicates("id", keep="last", inplace=True)

#### Caractéristiques inutiles
#### ------------------------------

adult1.drop(["occupation"], axis=1, inplace=True)
adult34.drop(["id"], axis=1, inplace=True)

#### Conflits de valeurs
#### -------------------------

dic = {
    "Never-married": "single",
    "Married-civ-spouse": "married",
    "Married-spouse-absent": "married",
    "Married-AF-spouse": "married",
    "Divorced": "divorced",
    "Separated": "divorced",
    "Widowed": "widowed"
}
adult1["marital-status"] = adult1["marital-status"].map(dic)
adult2["marital-status"] = adult2["marital-status"].map(dic)

print adult1["sex"].unique()
print adult2["sex"].unique()
print adult34["sex"].unique()

adult1["sex"] = adult1["sex"].map({"Female": "F", "Male": "M"})
adult1["class"] = adult1["class"].map({"<=50K": "N", ">50K": "Y"})

#### Fusionnement des schémas
#### -------------------------

adult = pandas.concat([adult1, adult2, adult34], ignore_index=True)

####################################
### II-6-3 Nétoyage des données
####################################

# afficher le nombre des valeurs indéfinies pour chaque colonne
#print adult.isnull().sum()

adult.dropna(subset=["workclass", "education", "marital-status", "sex", "hours-per-week", "class"], inplace=True)

adult["age"] = pandas.to_numeric(adult["age"])
adult["age"] = adult.groupby(["class", "education"])["age"].transform(lambda x: x.fillna(int(round(x.mean()))))

adult["hours-per-week"] = pandas.to_numeric(adult["hours-per-week"])

adult.to_csv("adult_test.csv")
#print adult.dtypes
#print adult.isnull().sum()
#print adult["marital-status"].unique()
#print adult["sex"].unique()
#print adult["class"].unique()
