import requests

def checkweather(city):
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        return response.text
    except:
        return "Weather lookup failed."
