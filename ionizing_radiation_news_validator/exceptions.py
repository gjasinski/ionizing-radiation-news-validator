class Not200Code(Exception):
    def __init__(self, value="Returned http code is not 200"):
            self.value = value

    def __str__(self):
        return repr(self.value)

class InvalidArgument(Exception):
    def __init__(self, value = ""):
            self.value = "Invalid argument. " + value

    def __str__(self):
        return repr(self.value)

class NLPNewsCheckerNotValid(Exception):
    def __init__(self, value="Given instance of NLPNewsChecker is not valid, please check if you found date and countries in article"):
            self.value = value

    def __str__(self):
        return repr(self.value)

class CityNotFound(Exception):
    def __init__(self, value="I can't find this city. Please search only major cities/capital cities"):
            self.value = value

    def __str__(self):
        return repr(self.value)
