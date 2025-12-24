from phonenumbers import geocoder
import phonenumbers

def getcountryorcity(phonenumber, shortnamedlanguage):
    phonenumberparsed = phonenumbers.parse(phonenumber)
    return geocoder.description_for_number(phonenumberparsed, lang=shortnamedlanguage)
