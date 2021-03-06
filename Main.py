# -*- coding: utf-8 -*-

import urllib.request
import pandas as pd
import re
import json
import os
import ssl
import time
from TripAdvisor import *
import requests
from os import listdir
from os.path import isfile, join
import numpy as np
from http import cookiejar

# -----------------------------------------------------------------------------------------------------------------------


def waitForEnd(threads):

    for i in threads:
        i.join()

    print("END")
    print("-"*50)


def stepOne(CITY):

    TAH = TripAdvisorHelper()

    PAGES = TAH.getRestaurantPages(CITY)

    n_threads = 24
    threads = []

    len_data = PAGES
    len_data_thread = len_data // n_threads

    for i in range(n_threads):
        data_from = i * len_data_thread
        data_to = (i + 1) * len_data_thread
        if (i == n_threads - 1):
            data_to = len_data

        temp_thread = TripAdvisor(i, "Thread-" + str(i), i, data=[data_from, data_to], city=CITY, step=0)
        threads.append(temp_thread)
        threads[i].start()

    waitForEnd(threads)

    TAH.joinRestaurants(CITY)


def stepTwo(CITY, LANG):

    TAH = TripAdvisorHelper()

    n_threads = 24
    threads = []

    data = pd.read_pickle("restaurants-"+CITY.lower().replace(" ", "")+".pkl")
    # data = data.loc[data.id==1649152]

    len_data = len(data)
    len_data_thread = len_data // n_threads

    for i in range(n_threads):

        data_from = i * len_data_thread
        data_to = (i + 1) * len_data_thread
        if (i == n_threads - 1):
            data_to = len_data
        data_thread = data.iloc[data_from:data_to, :].reset_index()

        temp_thread = TripAdvisor(i, "Thread-" + str(i), i, data=data_thread, city=CITY, step=1, lang=LANG)
        threads.append(temp_thread)
        threads[i].start()

    waitForEnd(threads)

    TAH.joinReviews(CITY)


def stepThree(CITY, LANG):

    TAH = TripAdvisorHelper()

    n_threads = 20
    threads = []

    data = pd.read_pickle("revIDS-"+CITY.lower().replace(" ", "")+".pkl")
    # data = data.loc[(data.title == '') | (data.text.isnull())]  #  Si no tienen titulo o texto

    len_data = len(data)
    len_data_thread = len_data//n_threads

    for i in range(n_threads):

        data_from = i*len_data_thread
        data_to = (i+1)*len_data_thread
        if(i == n_threads-1):
            data_to = len_data
        data_thread = data.iloc[data_from:data_to, :].reset_index()

        temp_thread = TripAdvisor(i, "Thread-"+str(i), i, data=data_thread, lang=LANG, city=CITY, step=2)
        threads.append(temp_thread)
        threads[i].start()

    waitForEnd(threads)
    TAH.joinAndAppendFiles(CITY)


def stepFour(CITY):

    n_threads = 24
    threads = []

    PATH = "/media/nas/pperez/data/TripAdvisor/" + CITY.lower().replace(" ", "") + "_data/"

    data = pd.read_pickle(PATH+"reviews.pkl")

    len_data = len(data)
    len_data_thread = len_data // n_threads

    for i in range(n_threads):

        data_from = i * len_data_thread
        data_to = (i + 1) * len_data_thread
        if (i == n_threads - 1):
            data_to = len_data
        data_thread = data.iloc[data_from:data_to, :].reset_index(drop=True)

        temp_thread = TripAdvisor(i, "Thread-" + str(i), i, city=CITY, data=data_thread, step=3)
        threads.append(temp_thread)
        threads[i].start()


def getStats(CITY):

    FOLDER = "/media/nas/pperez/data/TripAdvisor/%s_data/" % CITY.lower()
    IMG_FOLDER = FOLDER + "images/"

    RST = pd.read_pickle(FOLDER + "restaurants.pkl")
    USRS = pd.read_pickle(FOLDER + "users.pkl")
    RVW = pd.read_pickle(FOLDER + "reviews.pkl")

    #  A??adir columnas con n??mero de im??genes y likes
    RVW["num_images"] = RVW.images.apply(lambda x: len(x))
    RVW["like"] = RVW.rating.apply(lambda x: 1 if x > 30 else 0)
    RVW["restaurantId"] = RVW.restaurantId.astype(int)

    # A??adir columnas a los restaurantes
    RST["id"] = RST.id.astype(int)
    RST["reviews"] = 0

    print("Retaurantes: " + str(len(RST.id.unique())))
    print("Usuarios: " + str(len(USRS.loc[(USRS.id != "")])))
    print("Reviews: " + str(len(RVW.loc[(RVW.userId != "")])))
    print("Im??genes: " + str(sum(RVW.num_images)))
    print("")

    #  Quedarse con las que tienen im??genes
    RVW = RVW.loc[RVW.num_images > 0]

    #  Para cada restaurante
    # for i, r in RVW.groupby("restaurantId"):
    #     likes = (sum(r.like) * 100) / len(r)
    #     RST.loc[RST.id == i, ["like_prop", "reviews"]] = likes, len(r)

    #  Quedarse con los que tienen reviews con im??gen
    RST = RST.loc[RST.reviews > 0]

    print("Restaurantes (con im??gen): ", len(RST))
    print("Usuarios (con im??gen): ", len(RVW.userId.unique()))
    print("Reviews (con im??gen): ", len(RVW))
    print("")
    print("Porcentaje de likes: ", sum(RVW.like)/len(RVW)*100)

    RET = pd.DataFrame(columns=['user', 'likes', 'reviews'])

    for i, g in RVW.groupby("userId"):
        likes = sum(g.like)
        total = int(len(g))
        RET = RET.append({"user": i, "likes": likes, "reviews": total}, ignore_index=True)

    RET.to_csv("../../stats/user_stats_"+CITY.lower()+".csv")


# -----------------------------------------------------------------------------------------------------------------------

# CITY = "London"; LANG='en'
# CITY = "Paris"; LANG = 'fr'
# CITY = "New York City"; LANG = 'en'
# CITY = "Madrid"; LANG = 'es'
# CITY = "Barcelona"; LANG = 'es'
# CITY = "Gijon"; LANG = 'es'
CITY = "Malaga"; LANG = 'es'

# Descargar restaurantes
# --------------------------------------------------------------------------
# stepOne(CITY)
# rsts = pd.read_pickle("restaurants-malaga.pkl")

# Descargar reviews
# --------------------------------------------------------------------------
# stepTwo(CITY,LANG)
# rvws = pd.read_pickle("revIDS-malaga.pkl")

# Ampliar reviews
# --------------------------------------------------------------------------
# stepThree(CITY,LANG)

# Descargar imagenes
# --------------------------------------------------------------------------
# stepFour(CITY)

# Obtener estadisticas

getStats(CITY)

# TODO: USERS SIN ID, MISMO RESTAURANTE, 2 ID
