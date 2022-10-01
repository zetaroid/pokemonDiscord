class Shop_Item(object):

    def __init__(self, itemName, price, currency, item_type=None):
        self.itemName = itemName
        self.price = price
        self.currency = currency
        self.item_type = item_type
