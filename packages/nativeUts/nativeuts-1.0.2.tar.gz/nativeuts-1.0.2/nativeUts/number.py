from forbiddenfruit import curse



def numberToBr(self):
    return f"{self:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



curse(float, "numberToBr", numberToBr)