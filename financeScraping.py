#math/data vis
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

#web requests/html parsing
import requests
import regex as re
from bs4 import BeautifulSoup
from readability import Document #for SA/paywalled/login-restricted articles maybe

HTTPStatusCodes = {200: "OK", 406: "Not Acceptable", 429: "Request Limit Reached", 500: "Generic Error"}
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15"} #fake safari-based request

alphabets = "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"
digits = "([0-9])"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    if "..." in text: text = text.replace("...","<prd><prd><prd>")
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

#nlp-related
import nltk
import spacy
#tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
from textblob import TextBlob

#misc
import os
import time
from wordcloud import WordCloud
from termcolor import colored, cprint
colors = ["grey", "red", "green", "yellow", "blue", "magenta", "cyan"] #and white but it doesn't look good

arrayOfSecurities = [["CIBR", "NASDAQ", "First Trust NASDAQ Cybersecurity ETF"], ["ICLN", "NASDAQ", "iShares Global Clean Energy ETF"], ["AMZN", "NASDAQ", "Amazon.com"], [".INX", "INDEXSP", "S&P500"], [".DJI", "INDEXDJX", "Dow Jones Industrial Average"], ["WCLD", "NASDAQ", "WisdomTree Cloud Computing ETF"], ["SKYY", "NASDAQ", "First Trust Cloud Computing ETF"], ["CLOU", "NASDAQ", "Global X Cloud Computing ETF"], ["BOTZ", "NASDAQ", "Global X Robotics and Artificial Intelligence ETF"], ["ROBO", "NYSEARCA", "ROBO Global Robotics and Automation Index ETF"], ["ROBT", "NASDAQ", "First Trust Nasdaq AI and Robotics ETF"], ["QTUM", "NYSEARCA", "Defiance Quantum ETF"], ["VGT", "NYSEARCA", "Vanguard Information Technology Index Fund ETF"], ["QCLN", "NASDAQ", "First Trust NASDAQ Clean Edge Green Energy Idx Fd"], ["CNRG", "NYSEARCA", "SPDR S&P Kensho Clean Power ETF"], ["RAYS", "NASDAQ", "Global X Solar ETF"], ["FAN", "NYSEARCA", "First Trust Global Wind Energy ETF"], ["URA", "NYSEARCA", "Global X Uranium ETF"], ["HYDR", "NASDAQ", "Global X Hydrogen ETF"], ["BE", "NYSE", "Bloom Energy Corp"], ["HJEN", "NYSEARCA", "Direxion Hydrogen ETF"], ["HDRO", "NYSEARCA", "Defiance Next Gen H2 ETF"], ["HACK", "NYSEARCA", "ETFMG Prime Cyber Security ETF"], ["SOXX", "NASDAQ", "iShares Semiconductor ETF"], ["SMH", "NASDAQ", "VanEck Semiconductor ETF"], ["QCOM", "NASDAQ", "QUALCOMM, Inc."], ["TSM", "NYSE", "Taiwan Semiconductor Mfg. Co. Ltd."], ["MU", "NASDAQ", "Micron Technology, Inc."], ["AMD", "NASDAQ", "Advanced Micro Devices, Inc."], ["NVDA", "NASDAQ", "NVIDIA Corporation"], ["AVGO", "NASDAQ", "Broadcom Inc"], ["PANW", "NASDAQ", "Palo Alto Networks Inc"], ["ZS", "NASDAQ", "Zscaler Inc"], ["CRWD", "NASDAQ", "Crowdstrike Holdings Inc"], ["CYBR", "NASDAQ", "Cyberark Software Ltd"]]

def findCurrentSecurityPrice(tickerSymbol, stockExchange):
    url = f"https://www.google.com/finance/quote/{tickerSymbol}:{stockExchange}"; getRequest = requests.get(url, headers = headers)

    if getRequest.status_code == 200:
        soup = BeautifulSoup(getRequest.text, "html.parser")
        price = soup.find("div", {"class": "YMlKec fxKbKc"})
        if type(price) == None:
            raise ValueError(f"Could not find specified HTML class with price information for ticker {tickerSymbol}")
        else:
            return 1, float(price.text.replace("$", "").replace(",", ""))
    else:
        return HTTPStatusCodes[getRequest.status_code]

def printCurrentSecurityPrices(arrayOfSecurities):
    _colorCounter = 0
    for security in arrayOfSecurities:
        color = colors[_colorCounter % 7]
        _colorCounter += 1
        print(colored(f"{security[2]}", color), "current price is", colored(f"{findCurrentSecurityPrice(security[0], security[1])[1]}", color))

def scrapeNewsArticleURLs(security, websiteVariable):
    tickerSymbol, stockExchange, fullName = security
    if stockExchange == "NYSEARCA":
        stockExchange = "NYSEMKT"
    elif stockExchange == "NASDAQ":
        pass
    else:
        raise ValueError(f"{stockExchange} is not supported. Use 'NYSEARCA' or 'NASDAQ' securities only.")

    if "iShares" in fullName or "ETF" in fullName or "First Trust" in fullName:
        isETF = True
    else:
        isETF = False

    if websiteVariable == "MF":
        url = f"https://www.fool.com/quote/{stockExchange}/{tickerSymbol}/"; getRequest = requests.get(url, headers = headers)
        if getRequest.status_code == 200:
            soup = BeautifulSoup(getRequest.text, "html.parser"); articlesURLs = []

            featArticlesDiv = soup.find("div", {"class": "flex flex-col md:flex-row gap-16px mb-12px"}); print(featArticlesDiv)
            for a in featArticlesDiv.find_all("a", href = True):
                articlesURLs.append("https://www.fool.com" + a["href"])

            otherArticlesDiv = soup.find("div", {"class": "page"})
            for a in otherArticlesDiv.find_all("a", href = True):
                articlesURLs.append("https://www.fool.com" + a["href"])

            return articlesURLs
        else:
            return HTTPStatusCodes[getRequest.status_code]
    elif websiteVariable == "Z": #maybe unscrapable?
        if not isETF:
            url = f"https://www.zacks.com/stock/quote/{tickerSymbol}/"; getRequest = requests.get(url, headers = headers)
            if getRequest.status_code == 200:
                soup = BeautifulSoup(getRequest.text, "html.parser")
                zacksNews = soup.find("ul", {"id": "news-tab-1"})
                return zacksNews
            else:
                return HTTPStatusCodes[getRequest.status_code]
        else:
            url = f"https://www.zacks.com/funds/etf/{tickerSymbol}/profile"; getRequest = requests.get(url, headers = headers)
            if getRequest.status_code == 200:
                soup = BeautifulSoup(getRequest.text, "html.parser")
                zacksNews = soup.find("section", {"id": "stocks_other_news"})
                return zacksNews
            else:
                return HTTPStatusCodes[getRequest.status_code]
    elif websiteVariable == "SA": #not working
        url = f"https://seekingalpha.com/symbol/{tickerSymbol}"; getRequest = requests.get(url, headers = headers)
        if getRequest.status_code == 200:
            soup = BeautifulSoup(getRequest.text, "html.parser"); articlesURLs = []
            analysisDiv = soup.find("div", {"class": "cbvA"}) #can't find it?
            
            #for art in analysisDiv.find_all("article", {"class": "vdA hiA bgA biX biBK nxA biL biCE nxA biL biCE nxE nxE vdB"}):
            #    articlesURLs.append(art)
            #return articlesURLs
        else:
            return HTTPStatusCodes[getRequest.status_code]
    elif websiteVariable == "B": #not working
        url = f"https://www.benzinga.com/quote/{tickerSymbol}"; getRequest = requests.get(url, headers = headers)
        if getRequest.status_code == 200:
            soup = BeautifulSoup(getRequest.text, "html.parser"); articlesURLs = []
            newsCol = soup.find_all("div", {"class": "ContentHeadline__Container-sc-30bi4w-0 hwGFPL py-2 content-headline"}) #also not finding anything?
        else:
            return HTTPStatusCodes[getRequest.status_code]
    else:
        raise ValueError(f"{websiteVariable} is not a valid website variable. Use 'MF', 'Z', 'SA', or 'B'.")

def newsToText(url):
    if not url:
        raise ValueError("url DNE")
    elif "fool.com" in url:
        getRequest = requests.get(url, headers = headers)
        soup = BeautifulSoup(getRequest.text, "html.parser")
        articleString = ""

        firstSentence = soup.find("h2", {"class": "font-light leading-10 text-h3 text-gray-1100 mb-32px"}).text
        articleString += firstSentence
        tablesArray = []; captionsArray = []

        textBody = soup.find("div", {"class": "tailwind-article-body"})
        tables = soup.find_all("div", {"class": "table-responsive"})
        captions = soup.find_all("p", {"class": "caption"})

        for paragraph in textBody:
            articleString += (paragraph.text)

        #remove unnecessary characters
        for table in tables:
            tablesArray.append(table.text)
        for caption in captions:
            captionsArray.append(caption.text)
        
        for table in tablesArray:
            articleString = articleString.replace(table, "")
        for caption in captionsArray:
            articleString = articleString.replace(caption, "")
        articleString = re.sub(r'\n\s*\n', '\n\n', articleString)

        return articleString
    elif "seekingalpha.com" in url:
        pass
    elif "benzinga.com" in url:
        pass
    elif "zacks.com" in url:
        pass
    else:
        raise ValueError(f"{url} is not a valid website. Use fool/benzinga/seekingalpha/zacks.com urls")

def scrapeNewsArticlesSentences(security, websiteVariable):
    articleURLs = scrapeNewsArticleURLs(security, websiteVariable)
    if type(articleURLs) == str:
        raise ValueError(f"HTTP Status Code: {articleURLs}")
    else:
        articles = []
        for url in articleURLs:
            article = newsToText(url)
            sentences = split_into_sentences(article)
            articles.append(sentences)

        return articles

def analyzeSentiments(artAsSentencesArray):
    sentiments = []
    for artAsSentences in artAsSentencesArray:
        for sentence in artAsSentences:
            txt = TextBlob(sentence)
            a = txt.sentiment.polarity
            b = txt.sentiment.subjectivity
            sentiments.append([sentence, a, b])
    return sentiments

def avgSentimentPolarity(security, websiteVariable, showPlot = False):
    while True:
        try:
            artAsSentencesArray = scrapeNewsArticlesSentences(security, websiteVariable)
            sentiments = analyzeSentiments(artAsSentencesArray)
            dfTextblob = pd.DataFrame(sentiments, columns = ["Sentence", "Polarity", "Subjectivity"])
            polarityCol = dfTextblob["Polarity"]

            if showPlot:
                plt.plot(polarityCol)
                plt.show()
            break
        except AttributeError:
            continue
        except ValueError:
            raise ValueError("Wrong HTTP code")

    return sum(polarityCol) / len(polarityCol)

tup = list(reversed(range(1, 11)))
print(tup)

#printCurrentSecurityPrices(arrayOfSecurities)
#print(scrapeNewsArticleURLs(["CIBR", "NASDAQ", "First Trust NASDAQ Cybersecurity ETF"], "MF"))
#print(newsToText("https://www.fool.com/investing/2021/10/16/this-etf-could-help-grow-any-retirement-account/"))
#print(scrapeNewsArticlesSentences(["CIBR", "NASDAQ", "First Trust NASDAQ Cybersecurity ETF"], "MF"))
#print(avgSentimentPolarity(["CIBR", "NASDAQ", "First Trust NASDAQ Cybersecurity ETF"], "MF"))

#sns.displot(dfTextblob["Subjectivity"], height = 5, aspect = 1.8)
#plt.xlabel("Sentence Subjectivity (Textblob)")
#sns.plt.show()