import requests
import re
from bs4 import BeautifulSoup

HTTPStatusCodes = {200: "OK", 406: "Not Acceptable", 429: "Request Limit Reached", 500: "Generic Error"}
TIWEra = ["This Is Why", "The News", "C'est Comme Ca"]

class Discography:
    def __init__(self, artist, songList):
        self.artist = artist
        self.songList = songList

def parseForURL(plainString):
    dashRegex = "[ /]"
    removeRegex = "[':()]"
    coverRegex = " \(.*Cover\)$"
    
    parsed = re.sub(coverRegex, "", plainString)
    parsed = re.sub(removeRegex, "", parsed)
    parsed = re.sub(dashRegex, "-", parsed)
    return parsed

def rawHTMLLyrics(songTitle, artist):
    songTitle = parseForURL(songTitle)
    artist = parseForURL(artist)
    url = f"https://genius.com/{artist}-{songTitle}-lyrics"
    getReq = requests.get(url)

    try:
        soup = BeautifulSoup(getReq.text, "html.parser")
        rawLyrics = soup.find_all("div", {"data-lyrics-container": "true", "class": "Lyrics__Container-sc-1ynbvzw-6 YYrds"})
        if type(rawLyrics) == None:
            raise ValueError(f"Could not find specified HTML class with lyrics on {url}")
        else:
            return rawLyrics
    except KeyError:
        print("why the hell is this never printed yet i run into exceptions without the except block huh beautifulsoup")

def parseHTMLLyrics(rawHTML):
    strippedHTML = ""
    for i in range(len(rawHTML)):
        strippedHTML += rawHTML[i].text
    rawHTML = strippedHTML

    verseChorusRegex = r"\[.+?\]"
    lineBreakRegex = r"([a-z])([A-Z])"
    lineBreakEdgeCaseIRegex = r"(I)([A-Z])" # in case a line ends with the word "I"
    lineBreakEdgeCaseRParenRegex = r"(\))([^ ]+)" # in case a line ends with a closed parentheses
    lineBreakEdgeCaseLParenRegex = r"([^ |\n]+)(\()" # in case a line starts with an open parentheses
    lineBreakEdgeCasePuncRegex = r"([\?\!\—])(.)" # in case a line ends with !, -, or ?
    lineBreakEdgeCaseApostRegex = r"([a-z|A-Z])([\'])([A-Z])" # in case a line begins with an apostrophe

    breakLineRegex = r"\1\n\2"

    parsed = re.sub(verseChorusRegex, "", rawHTML)
    parsed = re.sub(lineBreakRegex, breakLineRegex, parsed)
    parsed = re.sub(lineBreakEdgeCaseIRegex, breakLineRegex, parsed)
    parsed = re.sub(lineBreakEdgeCaseRParenRegex, breakLineRegex, parsed)
    parsed = re.sub(lineBreakEdgeCaseLParenRegex, breakLineRegex, parsed)
    parsed = re.sub(lineBreakEdgeCasePuncRegex, breakLineRegex, parsed)
    parsed = re.sub(lineBreakEdgeCaseApostRegex, r"\1\n\2\3", parsed)
    return parsed

def rawHTMLSongList():
    url = "https://paramore.fandom.com/wiki/List_of_Songs"
    getReq = requests.get(url)

    if getReq.status_code == 200:
        soup = BeautifulSoup(getReq.text, "html.parser")
        rawSongList = soup.find("div", {"class": "mw-parser-output"}).find_all("li")
        if type(rawSongList) == None:
            raise ValueError("Couldn't scrap song lyrics from paramore.fandom.com")
        else:
            return rawSongList
    else:
        raise ValueError(f"HTTP request failed with code {HTTPStatusCodes[getReq.status_code]}")

def parseSongList(songs):
    ParamoreDiscog = Discography("Paramore", TIWEra.copy())
    HayleyDiscog = Discography("Hayley Williams", [])

    stopRegex = r"Teenagers"
    excludeParenRegex = r"(?i)\(.*[edit|mix|acoustic|demo|simlish|20].*\)$"
    numListRegex = r"^[0-9]"

    Hayley = False
    for i in range(len(songs)):
        song = songs[i].text
        if song == "26":
            ParamoreDiscog.songList.append("26")
            continue
        if song == 'Z and T presents "Baby Come Back 2 Me"':
            Hayley = True
            continue
        
        notSong1 = re.search(excludeParenRegex, song)
        notSong2 = re.search(numListRegex, song)
        lastSong = re.search(stopRegex, song)

        if lastSong is not None:
            break
        elif notSong1 is not None:
            pass
        elif notSong2 is not None:
            pass
        else:
            if Hayley:
                HayleyDiscog.songList.append(song)
            else:
                ParamoreDiscog.songList.append(song)

    return ParamoreDiscog, HayleyDiscog

ParamoreSongs, HayleySongs = parseSongList(rawHTMLSongList())

def countOccurrence(occurrenceRegex, discog):
    occurrence = 0
    songList = discog.songList
    artist = discog.artist

    maxOccurrence = 0; maxOccurrenceSong = ""
    for song in songList:
        rawLyrics = rawHTMLLyrics(song, artist)
        lyrics = parseHTMLLyrics(rawLyrics)
        allMatches = re.findall(occurrenceRegex, lyrics)
        matches = len(allMatches)
        occurrence += matches

        if matches > maxOccurrence:
            maxOccurrence = matches
            maxOccurrenceSong = song
        print(f"{song} has {matches} matches")

    print(f"Song with most matches is {maxOccurrenceSong} with {maxOccurrence} matches")
    return occurrence

mascPronounsRegex = r"(?i)\bhe\b|\bhim\b|\bhis\b"
secondPersonPronounsRegex = r"(?i)\byou\b|\byour\b|\byourself\b|\byours\b"
firstPersonPronounsRegex = r"(?i)\bus\b|\bme\b|\bi\b|\bwe\b|\bmine\b|\bours\b|\bour\b|\bmyself\b|\bourselves\b|\bmy\b"
femPronounsRegex = r"(?i)\bshe\b|\bher\b|\bhers\b"
wordsRegex = r"\b[\n| ]\b" # add +1 for each song since last word isn't counted
questionRegex = r"\?"
curseRegex = r"\bfuck\b|\bshit\b|\bcrap\b|\bbitch\b|\bdick\b|\bass\b|\bcunt\b|\basshole\b|\bpussy\b|\bfucker\b|\bfucking\b|\bshitty\b"

def countAndSummary(regex, discog):
    count = countOccurrence(regex, discog)
    print(f"{count} matches total. On average, {count / len(discog.songList)} uses per song.")
    print(f"{len(discog.songList)} songs in this discography in total.")

countAndSummary(curseRegex, HayleySongs)