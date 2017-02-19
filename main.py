from yahoo_finance import Share
import time, json, sys, ssl, math

class Wallet():

    def __init__(self):
        a = 1

    def buy(self, ID, price, numToBuy):
        obj = ShareObj(ID)
        obj.refresh()

        if(self.cash > price): #if you have sufficient funds
            with open('data.json', 'r+') as file:
                try:
                    data = json.load(file) # read file
                except json.decoder.JSONDecodeError:
                    print('Error loading JSON - Check your JSON file')
                    sys.exit(0)

                # wipe file
                file.seek(0)
                file.truncate()

                for i in range(numToBuy):
                    try: #to allow for multiple shares to be done you could like set a variable of percent change in the json, read that. if that *= 0.05 isn't less that the current percent change, don't buy again
                        data["shares"].append({ # add new price to appropriate id
                            "id": obj.getID(),
                            "price": price
                        })
                    except AttributeError:
                        # uh oh!!! that ID doesnt exist yet!! just create it :)
                        data['shares'].append({
                            "id": obj.getID(),
                            "price": price
                        })
                    self.setCash(self.cash - price) #buy that shit


                data = str(data).replace("'", '"')

                file.write(data)
                file.close()

                self.writeCash()

    def sell(self, ID, sellPrice):
        obj = ShareObj(ID)
        obj.refresh()

        with open('data.json', 'r+') as file: #open file
            try:
                data = json.load(file) # read file
            except json.decoder.JSONDecodeError:
                print("Error - Check JSON file!") #error check -- json file error
                sys.exit(0)

            file.seek(0) #wipe file
            file.truncate()

            if not (self.isOwned(obj.getID(), data)):
                data = str(data).replace("'", '"') #clean up json

                file.write(data)#write to json
                file.close() #close json

                return

            shareAmount = [] #list of indexes of items to be removed
            counter = 0 #

            for i in range(len(data["shares"])):
                if(data["shares"][i]["id"] == obj.getID()): #create list of indexes of shares to be removed and sold
                    shareAmount.insert(0,i)

            for i in range(len(shareAmount)):
                del data["shares"][shareAmount[i]] #sell all shares of id

            data = str(data).replace("'", '"') #clean up json

            file.write(data)#write to json
            file.close() #close json

            self.setCash(self.cash + sellPrice*int(len(shareAmount)))
            self.writeCash()

    def getCash(self):
        return self.cash

    def setCash(self, value):
        self.cash = value

    def writeCash(self):
        with open('data.json', 'r+') as file: #open file
            try:
                data = json.load(file) # read file
                data["userdata"]["wallet"] = self.cash
            except ValueError:
                raise ValueError('Cannot read JSON file')

            file.seek(0)
            file.truncate()

            data = str(data).replace("'", '"')

            file.write(data)
            file.close()

    def isOwned(self, ID, data):
        with open('data.json', 'r+') as file: # open file
            for i in range(0,len(data["shares"])): #for the amount of shares recorded in json file
                try:
                    if(data["shares"][i]["id"] == ID): #checks if valid id, as in, does this share exist in the JSON?
                        return True
                except AttributeError: #if error, report it
                    print("ERROR - SELLING - share ID doesn't exist.")
                    return False
        return False

class ShareObj(object):
    def __init__(self, ID):
        self.id = ID
        self.share = Share(self.id)
        self.refresh

    def getPrice(self):
        return self.share.get_price()

    def getOpenPrice(self):
        return self.share.get_open()

    def getChange(self):
        if(self.share.get_percent_change() == None):
            return 0
        else:
            percent = (self.share.get_percent_change()[:-1])
            return float(percent)

    def getChangeFormatted(self):
        self.share.get_percent_change()

    def getID(self):
        return self.id

    def refresh(self):
        self.share.refresh()

    def getHistorical(self,date1, date2):
        return self.share.get_historical(date1,date2)

    def getCalculatedChange(self, open, close):
        return ((close - open)/open)*100

w = Wallet()

stocksToWatch = "TMUS"

ssl._create_default_https_context = ssl._create_unverified_context

shre = ShareObj(stocksToWatch)
historicalData = shre.getHistorical("2016-11-21", "2017-02-17")

total = 0
for l in range(len(historicalData)):
        total += shre.getCalculatedChange(float(historicalData[l]["Open"]), float(historicalData[l]["Close"]))

percentChange = (total/len(historicalData))+1

w.setCash(10000)
total = 1
for i in range(len(historicalData)):
    closeVar = float(historicalData[i]["Close"]) #is this optimization??? the world may never know
    openVar = float(historicalData[i]["Open"])

    iterationsPercentChange = shre.getCalculatedChange(openVar, closeVar)

    if(iterationsPercentChange < (-1*percentChange)): # if it is less than the percent change we're looking for, do this
        w.sell(shre.getID(), openVar)
    elif(iterationsPercentChange > percentChange): # if change for current day is higher than average
        sharesBought = int((((float(historicalData[i]["High"]) + float(historicalData[i]["Low"]) + closeVar)/3)*2)-closeVar)
        print("["+time.strftime("%H:%M:%S")+"] [CASH]\t\t"+str(w.getCash()))
        print("["+time.strftime("%H:%M:%S")+"] [SHARES]\t ["+str(total)+"]\t"+str(sharesBought))

        w.buy(shre.getID(), openVar, sharesBought)

        total += 1

w.sell(shre.getID(), closeVar)
print("Ending total: "+str(w.getCash()))
