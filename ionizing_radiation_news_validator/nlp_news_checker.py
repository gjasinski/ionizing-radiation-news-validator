import requests
import json
import re
from exceptions import Not200Code


class NLPNewsChecker:
    def __init__(self, url):
        self.__url = url
        self.__download_page()

    def __download_page(self):
        r = requests.get(self.__url)
        if(not r.status_code == 200):
            raise Not200Code()
        else:
            self.__article_data = r.text

    # Extract date of article and save it in YYYY-MM-DD format
    def get_article_date(self):
        reg1 = re.search("[0-9]{2}-[0-9]{2}-[0-9]{4}", self.__article_data)
        reg2 = re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", self.__article_data)
        if not (reg1 or reg2):
            print("I can't find date of article")
        else:
            if reg1:
                (date_s, date_e) = reg2.span()
                self.date = self.__article_data[date_s + 6:date_e] + \
                    self.__article_data[date_s + 2:date_e - 2] + \
                    self.__article_data[date_s:date_s + 2]
            if reg2:
                (date_s, date_e) = reg2.span()
                self.date = self.__article_data[date_s:date_e]
            print("Article date: %s" % self.date)

    def __get_european_countries_with_capital_cities(self):
        r = requests.get("https://restcountries.eu/rest/v2/region/europe")
        if(not r.status_code == 200):
            raise Not200Code()
        json_data = json.loads(r.text)
        self.country_and_city = dict()
        for o in json_data:
            self.country_and_city[o["name"]] = o["capital"]
        self.country_and_city["Ukraine"] = "Chernobyl"  # This is exception

    def __scan_text(self, list_of_words):
        result = list()
        for word in list_of_words:
            reg_res = re.search(word, self.__article_data)
            if reg_res:
                result.append(word)
        return result

    # Extract names of countries enumerated in article
    def find_countries_named_in_article(self):
        self.__get_european_countries_with_capital_cities()
        self.enumerated_countries = self.__scan_text(
            self.country_and_city.keys())
        if self.enumerated_countries:
            print("Enumerated european countries:")
            for country in self.enumerated_countries:
                    print(country)
        else:
            print("There are no enumerated country in article.")

    # Checks if key words are in article
    def is_this_article_about_radiation(self):
        if self.__scan_text(["solar radiation"]):
            print("This article is about solar radiation")
            return
        f = open("words_in_favour.json", 'r')
        json_data = json.loads(f.read())
        word_list = list()
        for word in json_data:
            word_list.append(word["word"])
        if len(self.__scan_text(word_list)) > 4:
            print("This article is about nuclear radiation")
        else:
            print("This article is not about nuclear radiation")
        self.article_about_radiation = len(self.__scan_text(word_list)) > 4
