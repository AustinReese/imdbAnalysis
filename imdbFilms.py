# Austin Reese - CS 320
#
# For this exam I chose to focus on the correlation between the year a film was released and it's reception.
# Metascore is more aimed towards critics, while IMDb rating is aimed towards the average joe with a computer.
# I created four similar graphs, two bar graphs displaying average rating by year and two scatter plots displaying
# entries graphed by year/rating (with the opposite rating transposed as a colormap so the differences between
# Metascore and IMDb rating could be examined. There was a somewhat noticable pattern when comparing metascore
# and year, as older films tended to have higher metascores. This was confirmed when I caclculated the correlation
# coefficient to be -.45, which indicates some weak negative correlation. The correlation was far less prevelant when
# analyzing IMDb ratings, as the coefficient was a mere -.22. In conclusion, it's safe to assume from this data that
# critics tend to rate older films higher than newer films, while the general public of IMDb simply didn't care quite
# as much. This is emphasized by the fact that many films with high IMDb ratings had far lower Metascores, while the
# opposite never occured in the same extreme
#
# My topImdb.csv can be found here: https://knuth.luther.edu/~reesau01/topImdb.csv

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os.path
import webbrowser 
import time
from lxml import html

s = requests.Session()

def getTopImdb():
    print("Fetching data from IMDb...")
    page = 1
    titles = []
    while page <= 5:
        imdb = s.get("https://www.imdb.com/list/ls003073623/?sort=list_order,asc&st_dt=&mode=detail&page={}".format(page))
        tree = (html.fromstring(imdb.content))
        titles = titles + tree.xpath("//h3[@class='lister-item-header']//a/text()")
        page += 1
    print("{} titles scraped".format(len(titles)))
    return titles

def getMovieData(topImdb):
    runs = 0
    jsonFrames= []
    print("Fetching data from OMDb API...")
    for film in topImdb:
        runs += 1
        film = film.replace(" ", "+")
        page = s.get("http://www.omdbapi.com/?apikey=fdab2733&t={}".format(film))
        jsonFrame = json.loads(page.content)
        try:
            jsonFrame["Title"]
        except:
            jsonFrame["Title"] = film.replace("+", " ")
        try:
            jsonFrame = pd.DataFrame(jsonFrame)
        except:
            jsonFrame = pd.DataFrame(jsonFrame, index=[-1])
        try:
            jsonFrame = jsonFrame.drop(jsonFrame.index[2])
        except:
            pass
        try:
            jsonFrame = jsonFrame.drop(jsonFrame.index[1])
        except:
            pass
        jsonFrames.append(jsonFrame)
        if runs % 10 == 0:
            print("{}% complete".format(int(runs / len(topImdb) * 100)))
    movies = pd.concat(jsonFrames)
    movies.index = range(len(movies))
    print("{} pieces of data scraped successfully".format(runs))
    return movies
    

def normalizeRevenue(movieData):
    print("Fetching data from data.bls.gov to normalize box office revenue...")
    runs = 0
    for i, movie in movieData.iterrows():
        runs += 1
        box = movie["BoxOffice"]
        if box == "N/A" or box == np.nan:
            box = 0
        box = str(box).replace(",", "")
        box = str(box).replace("$", "")
        year = movie["Year"]
        try:
            box = int(box)
        except:
            box = 0
        if box > 9999999:
            maxVals = box / 9999999
            subBox = [9999999] * int(maxVals)
            decimal = maxVals - int(maxVals)
            subBox.append(decimal * 9999999)
            newPrice = 0
            for num in subBox:
                page = s.get("https://data.bls.gov/cgi-bin/cpicalc.pl?cost1={}&year1={}01&year2=201801".format(num, year))
                tree = (html.fromstring(page.content))
                thisPrice = set(tree.xpath('//span[@id="answer"]//text()'))
                thisPrice = thisPrice.pop()
                thisPrice = str(thisPrice).replace(",", "")
                thisPrice = str(thisPrice).replace("$", "")                
                newPrice += float(thisPrice)
        else:        
            page = s.get("https://data.bls.gov/cgi-bin/cpicalc.pl?cost1={}&year1={}01&year2=201801".format(box, year))
            tree = (html.fromstring(page.content))
            newPrice = set(tree.xpath('//span[@id="answer"]//text()'))
            if len(newPrice) == 0:
                newPrice = 0
            else:
                newPrice = newPrice.pop()
                newPrice = str(newPrice).replace(",", "")
                newPrice = str(newPrice).replace("$", "")
        movieData.at[i, "BoxOffice"] = newPrice
        if runs % 10 == 0:
            print("{}% complete".format(int(runs / len(movieData) * 100)))
    print("Data normalized successfully")
    return movieData
        
def cleanData(movieData):
    for i, movie in movieData.iterrows():    
        plot = movie["Plot"]
        try:
            plot = plot.replace(",", "")
            plot = plot.lower()            
        except:
            pass
        movieData.at[i, "Plot"] = plot
    return movieData

def writeCsv(movieData):
    movieData.to_csv("topIMDb.csv")
    print("topIMDb.csv written successfully")

def checkFileExists():
    exists = os.path.isfile("topIMDb.csv")
    exists = False
    if exists:
        return "topIMDb.csv"
    print("topIMDb.csv not found, press enter to access file from knuth, press any other key to remake the file to scrape the latest information")
    remain = input()
    if remain == "":
        return "http://knuth.luther.edu/~reesau01/topIMDb.csv"
    return True

def analyzeData(file):
    movieData = pd.read_csv(file)
    movieData['imdbVotes'].replace(regex=True,inplace=True,to_replace=',',value='')
    movieData.BoxOffice = movieData.BoxOffice.replace(0,np.nan)
    movieData.BoxOffice = movieData.BoxOffice.astype("float64")
    movieData.imdbVotes = movieData.imdbVotes.astype("float64")
    yearMeta = movieData.groupby(["Year"])["Metascore"]
    yearMeta.mean().plot(kind="bar")
    plt.title("Average Metascore by year")
    plt.xlabel("Year")
    plt.ylabel("Metascore")
    plt.show()
    yearImdb = movieData.groupby(["Year"])["imdbRating"]    
    yearImdb.mean().plot(kind="bar")
    plt.title("Average IMDb rating by year")
    plt.xlabel("Year")
    plt.ylabel("IMDb Rating")
    plt.show()
    print("Correlation Coefficient for Metascore and Year: {}".format(
    movieData.Metascore.dropna().corr(movieData.Year.dropna())))
    print("Correlation Coefficient for IMDb Rating and Year: {}".format(
    movieData.imdbRating.dropna().corr(movieData.Year.dropna())))    
    movieData.plot.scatter(x="Year", y="Metascore", c="imdbRating", colormap = "coolwarm")
    movieData.plot.scatter(x="Year", y="imdbRating", c="Metascore", colormap = "coolwarm")
    plt.show()    

    
    

def main():
    newFile = checkFileExists()
    if newFile == True:
        topImdb = getTopImdb()
        movieData = getMovieData(topImdb)
        movieData = normalizeRevenue(movieData)
        movieData = cleanData(movieData)
        writeCsv(movieData)
        print("Please run this program again")
        return
    analyzeData(newFile)

if __name__ == "__main__":
    main()