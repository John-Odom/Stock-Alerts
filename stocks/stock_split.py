class StockSplit:
    def __init__(self, date, ratio):
        self.date = date
        self.ratio = ratio

    def __repr__(self):
        return f"StockSplit(date={self.date}, ratio={self.ratio})"