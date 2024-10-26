import random
def toObject(filename):
  file = open(filename, "r")
  content = file.read()
  file.close()
  shares = content.split(",")
  shareList = []
  for share in shares:
    li = []
    for pair in share.split(";"):
      li.append(pair)
    shareList.append(li[:6])
  output =  {}
  for share in shareList:
    sub = {}
    for element in share:
      if element == share[0]:
        continue
      element = element.split(":")
      key = element[0].strip()
      value = float(element[1].strip())
      sub[key] = value
    key = share[0].split(":")
    key = key[1].strip()
    output[key] = sub
  return output

alphabets = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

def create(filename, names = alphabets):
  # Run To Reset shares.txt file with new values
  string = f"name : {names[0]};\nprice : {random.randint(250, 500)};\nquantity : 10000;\nbought : 0;\nsold : 0;\nrate : {(random.randint(95, 105) / 100)}\n,"
  for name in names:
    if name == names[0]:
      continue
    string = string + f"\nname : {name};\nprice : {random.randint(250, 500)};\nquantity : 10000;\nbought : 0;\nsold : 0;\nrate : {(random.randint(95, 105) / 100)}\n,"
  file = open(filename, "w")
  file.write(string[:-1])
  file.close()



def saveShares(filename, obj):
  keys = []
  for key in obj:
    keys.append(key)
  share = obj[keys[0]]
  string = f"name : {keys[0]};\nprice : {share['price']};\nquantity : {share['quantity']};\nbought : {share['bought']};\nsold : {share['sold']};\nrate : {share['rate']}\n,"
  for key in obj:
    share = obj[key]
    if key == keys[0]:
      continue
    string = string + f"\nname : {key};\nprice : {share['price']};\nquantity : {share['quantity']};\nbought : {share['bought']};\nsold : {share['sold']};\nrate : {share['rate']}\n,"
  file = open(filename, "w")
  file.write(string[:-1])
  file.close()
  
# create("shares.txt")
# print(toObject("shares.txt"))

# obj = toObject("shares.txt")
# saveShares("shares.txt", obj)