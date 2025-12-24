class numberconverter:
    def __init__(self,lakh):
        self.lakh = float(lakh)

    def lakh_to_million(self):
        return self.lakh / 1000000