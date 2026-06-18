from cs50 import SQL

from helpers import lookup

db = SQL("sqlite:///finance.db")

data = db.execute("SELECT symbol, shares FROM bought WHERE bought.user_id = (?)", 1)

for i in data:
    quote = lookup(i["symbol"])
    i["price"] = quote["price"]
    sum = int(i["shares"]) * float(i["price"])
    i["total"] = sum

for i in data:
    print(i)
