import requests

def checknet(host="https://www.google.com"):
    try:
        response = requests.get(host, timeout=10)
        if response.status_code == 200:
            return "You have internet.", True
        else:
            return "Connection failed.", False
    except:
        return "You don't have internet.", False

def sharedatatowebsite(url, json):
    requests.post(url, json=json)

def statuscode(var):
    return var.status_code

def gethtml(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers)
    return html.text

def getresponse(url):
    return requests.get(url)

def parsehtml(htmlvar):
    soup = BeautifulSoup(htmlvar, "html.parser")
    return soup

def getparsedhtml(parsedvar):
    return parsedvar.get_text()

def getjson(variable):
    return variable.json()

def getresponsewithtimeout(url, timeout=10):
    return requests.get(url, timeout=timeout)
