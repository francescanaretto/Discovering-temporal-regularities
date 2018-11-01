import json
import datetime
import gzip
import pandas as pd
import calendar
import numpy
import math

class EntropyModel:
    def __init__(self):
        self.customers = dict()
        self.entropies = dict()
        self.total_baskets = 0


    def read_json(self, filename):
        data = gzip.open(filename, 'r')
        for row in data:
            jdata = json.loads(row)
            jdata = eval(json.dumps(jdata))
            customer_id = jdata['customer_id']
            self.customers[customer_id] = dict()
            for date in sorted(jdata['data']):
                date_conv = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                date_conv = date_conv - datetime.timedelta(seconds=date_conv.second)
                self.customers[customer_id][date_conv] = dict()
                for shop_id in sorted(jdata['data'][date]):
                    self.customers[customer_id][date_conv][shop_id] = dict()
                    for item_id in sorted(jdata['data'][date][shop_id]['items']):
                        item_data = jdata['data'][date][shop_id]['items'][item_id]
                        self.customers[customer_id][date_conv][shop_id][item_id] = list()
                        quantity = item_data['quantity']
                        expenditure = item_data['amount']
                        self.customers[customer_id][date_conv][shop_id][item_id].append(quantity)
                        self.customers[customer_id][date_conv][shop_id][item_id].append(expenditure)
        data.close()
        return self

    def calculate_all_entropies(self, start, end):
        out_data = {}
        for customer in self.customers.keys():
            out_data[customer] = {}
            results = self.calculate_all_customer_entropies(customer, start, end)
            if len(results) == 0:
                out_data[customer]['baskets'] = 0
                out_data[customer]['items'] = 0
                out_data[customer]['amount'] = 0
                out_data[customer]['hour'] = 0
                out_data[customer]['shop_id'] = 0
            else:    
                out_data[customer]['baskets'] = results[0]
                out_data[customer]['items'] = results[1]
                out_data[customer]['amount'] = results[2]
                out_data[customer]['hour'] = results[3]
                out_data[customer]['shop_id'] = results[4]
        return out_data    

    def calculate_all_customer_entropies(self, customer_id, start, end):
        self.entropy_customer(customer_id, start, end)
        results = list() 
        if self.total_baskets < 1:
            return results   
        #number of purchases for each day of the week 
        results.append(self.entropy_number_baskets(customer_id))
        #number of items in the basket
        results.append(self.entropy_items(customer_id))
        #total amount of the purchasing
        results.append(self.entropy_amount(customer_id))
        #timing of the purchasing
        results.append(self.entropy_hour(customer_id))
        #shops in which the user go for purchasing
        results.append(self.entropy_shop_id(customer_id))
        self.total_baskets = 0
        return results

    #This function creates the stucture for each customer
    #a dictionary with the values of the different entropies evaluated 
    def entropy_customer(self, customer_id, start, end): 

        self.entropies[customer_id] = dict()

        #handle pointers to the strucure
        index_days = start.weekday() 
        index_week = 0  
        index_baskets = 0  

        #sort
        keys = self.customers[customer_id].keys()
        keys = sorted(keys)
        keys_date = list()

        for key in keys:
            keys_date.append(key.date())

        if index_days != 0:
            self.entropies[customer_id][index_week] = dict()

        for day in pd.date_range(start, end):
            if index_days == 0:
                index_week = index_week + 1
                self.entropies[customer_id][index_week] = dict()
                index_baskets = 0
            if day.date() in keys_date:
                for k in keys:
                    if day.date() == k.date():
                        date = k
                        break
                self.entropies[customer_id][index_week][index_days] = dict() 
                shop_id = self.customers[customer_id][date].keys()
                #number of item for each purchase
                items = len(self.customers[customer_id][date][shop_id[0]].keys())
                self.entropies[customer_id][index_week][index_days]['items'] = items
                #date of the purchase
                self.entropies[customer_id][index_week][index_days]['date'] = date
                #shop id in which the user went
                self.entropies[customer_id][index_week][index_days]['shop_id'] = shop_id
                #total amount of money for that basket
                items_id = self.customers[customer_id][date][shop_id[0]].keys()
                total_amount = 0
                for item in items_id:
                    total_amount += self.customers[customer_id][date][shop_id[0]][item][1]
                self.entropies[customer_id][index_week][index_days]['amount'] = total_amount    
                index_baskets = index_baskets + 1
            index_days = (index_days + 1) % 7
        for i in range (0, index_week+1):
            self.total_baskets += len(self.entropies[customer_id][i].keys()) 

    #Entropy based on the number of purchases for each day of the week 
    def entropy_number_baskets(self, customer_id):    
        index_week =  self.entropies[customer_id].keys() 
        entropy_values = list()
        for i in range(0, 7):
            entropy_values.append(0)
        for i in index_week:
            for d in range (0, 7):
                if d in self.entropies[customer_id][i].keys():
                    entropy_values[d] += 1
        for el in range(0, len(entropy_values)):
            entropy_values[el] = entropy_values[el]/float(self.total_baskets)
        entropy_baskets = 0
        for el in entropy_values:
            if el != 0:
                entropy_baskets += el* math.log(el)
        entropy_baskets = - entropy_baskets/float(math.log(len(entropy_values)))       
        return entropy_baskets              

    #Entropy based on the number of items for each basket
    def entropy_items(self, customer_id):
        index_week =  self.entropies[customer_id].keys() 
        entropy_values = list()
        for i in range(0, 4):
            entropy_values.append(0)       
        for i in index_week:
            for d in range (0, 7):
                if d in self.entropies[customer_id][i].keys():
                    value = self.entropies[customer_id][i][d]['items']
                    if value < 10:
                        entropy_values[0] += 1
                    elif  value < 25:
                        entropy_values[1] += 1
                    elif value < 50:
                        entropy_values[2] += 1
                    else:
                        entropy_values[3] += 1           
        for el in range(0, len(entropy_values)):
            entropy_values[el] = entropy_values[el]/float(self.total_baskets)
        entropy_items = 0
        for el in entropy_values:
            if el != 0.0:
                entropy_items += el* math.log(el)
        entropy_items = - entropy_items/float(math.log(len(entropy_values)))  
        return entropy_items  
    
    #Entropy based on the total amount of money spent for each purchase 
    def entropy_amount(self, customer_id):
        index_week =  self.entropies[customer_id].keys() 
        entropy_values = list()
        for i in range(0, 4):
            entropy_values.append(0)     
        for i in index_week:
            for d in range (0, 7):
                if d in self.entropies[customer_id][i].keys():
                    value = self.entropies[customer_id][i][d]['amount']
                    if value < 10:
                        entropy_values[0] += 1
                    elif  value < 25:
                        entropy_values[1] += 1
                    elif value < 50:
                        entropy_values[2] += 1
                    else:
                        entropy_values[3] += 1           
        for el in range(0, len(entropy_values)):
            entropy_values[el] = entropy_values[el]/float(self.total_baskets)
        entropy_amount = 0
        for el in entropy_values:
            if el != 0:
                entropy_amount += el* math.log(el)
        entropy_amount = - entropy_amount/float(math.log(len(entropy_values)))  
        return entropy_amount   

    #Entrpy based on the timing in which the user use to purchase 
    def entropy_hour(self, customer_id):
        index_week =  self.entropies[customer_id].keys() 
        entropy_values = list()
        for i in range(0, 4):
            entropy_values.append(0)       
        for i in index_week:
            for d in range (0, 7):
                if d in self.entropies[customer_id][i].keys():
                    date = self.entropies[customer_id][i][d]['date']
                    if date.hour < 11:
                        entropy_values[0] += 1
                    elif  date.hour < 15 :
                        entropy_values[1] += 1
                    elif date.hour < 18:
                        entropy_values[2] += 1
                    else:
                        entropy_values[3] += 1           
        for el in range(0, len(entropy_values)):
            entropy_values[el] = entropy_values[el]/float(self.total_baskets)
        entropy_dates = 0
        for el in entropy_values:
            if el != 0:
                entropy_dates += el* math.log(el)
        entropy_dates = - entropy_dates/float(math.log(len(entropy_values)))  
        return entropy_dates  

    #Entropy based on the number of diffenrent shops the user bought
    def entropy_shop_id(self, customer_id):
        index_week =  self.entropies[customer_id].keys() 
        entropy_values = dict()     
        for i in index_week:
            for d in range (0, 7):
                if d in self.entropies[customer_id][i].keys():
                    shop_id = self.entropies[customer_id][i][d]['shop_id']
                    shop_id = shop_id[0]
                    if shop_id in entropy_values.keys(): 
                        entropy_values[shop_id] += 1
                    else :    
                        entropy_values[shop_id] = 1
        result = list()                
        for k in entropy_values.keys():
            shop_id = entropy_values[k]
            result.append(shop_id/float(len(entropy_values.keys())))
        entropy_shop_id = 0
        for el in result:
            if el != 0:
                entropy_shop_id += el* math.log(el) 
        if len(result) == 1:
                entropy_shop_id = 0
        else:          
            entropy_shop_id = - entropy_shop_id/float(math.log(len(result)))  
        return entropy_shop_id   
