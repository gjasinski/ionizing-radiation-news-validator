import requests
import json
import re
class NLPNewsChecker:
    def __init__(self, url):
        self.url = url
        self.__download_page()

    def __download_page(self):
        r = requests.get(self.url)
        if(not r.status_code == 200):
            print("Can't download page " + r.status_code)
        else:
            self.article_data = r.text

    def get_date_of_article(self):
        reg1 = re.search("[0-9]{2}-[0-9]{2}-[0-9]{4}", self.article_data)
        reg2 = re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", self.article_data)
        if not (reg1 or reg2):
            print("I can't find date of article")
        else:
            if reg1:
                (date_s, date_e) = reg2.span()
                self.date = self.article_data[date_s + 6 :date_e] + self.article_data[date_s + 2 :date_e - 2] + self.article_data[date_s : date_s + 2]
            if reg2:
                (date_s, date_e) = reg2.span()
                self.date = self.article_data[date_s:date_e]

    def __get_european_countries_with_capital_cities(self):
        r = requests.get("https://restcountries.eu/rest/v2/region/europe")
        if(not r.status_code == 200):
            print("Can't download json with european countries and capital cities" + r.status_code)
            return
        json_data = json.loads(r.text)
        self.country_and_city = dict()
        for o in json_data:
            self.country_and_city[o["name"]] = o["capital"]
        self.country_and_city["Ukraine"] = "Chernobyl"  # This is exception

    def __scan_text(self, list_of_words):
        result = list()
        for word in list_of_words:
            reg_res = re.search(word, self.article_data)
            if reg_res:
                result.append(word)
        return result

    def find_countries_named_in_article(self):
        self.__get_european_countries_with_capital_cities()
        self.enumerated_countries = self.__scan_text(self.country_and_city.keys())
        if self.enumerated_countries:
            print("Enumerated european countries:")
            for country in self.enumerated_countries:
                    print(country)
        else:
            print("There is no enumerated european country in article.")

    def is_this_article_about_radiation(self):
        if self.__scan_text(["solar"]):
            print("This article is about solar radiation than nuclear radiation")
            return
        f = open("words_in_favour.json", 'r')
        json_data = json.loads(f.read())
        word_list = list()
        for word in json_data:
            word_list.append(word["word"])
        if len(self.__scan_text(word_list)) > 4:
            print("This article is about nuclear radiation")
