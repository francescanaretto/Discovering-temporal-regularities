import codecs, json
import datetime
import gzip
import pandas as pd
import calendar
import numpy
from kmeans import *


class Customers:
    def __init__(self):
        self.customers = dict()
        self.matrices = dict()
        self.centroids = dict()
        self.count_zero_matrices = 0

    #Create the dictionary customers from a json file
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

    # This function is a wrapper for 
    # the individual profile of each customer 
    # evaluates a global k means among the result of an individual k means
    def wrapper(self, start, end):
        out_data = {}
        for customer_id in self.customers.keys():
            self.create_individual_profile(customer_id, start, end)     
        #a collective k-means over all the matrices of all the clients
        kmeans = self.evaluate_global_kmeans()
        # for each individual matrix, the corresponding collective one is stored togher
        count = 0
        for customer_id in self.customers.keys():
            if customer_id in self.centroids.keys():
                for r in self.centroids[customer_id]:
                    out_data[customer_id] = {}
                    out_data[customer_id]['individual'] = r.tolist()
                    out_data[customer_id]['global'] = kmeans.cluster_centers_[kmeans.labels_[count]].tolist()
                    count += 1
                if self.count_zero_matrices != 0:
                    out_data[customer_id]['zeros'] = self.count_zero_matrices    
            else:
                out_data[customer_id] = {}
                out_data[customer_id]['zeros'] = self.count_zero_matrices
        return out_data
        

    # Individual profile creation 
    def create_individual_profile(self, id, start, end):
        index_week = self.create_matrices(id, start, end)
        results = self.conform_data_kmeans(id, index_week)   
        #case for clients with just one week of purchasing 
        if results.size < 28:
            return results   
        #call for individual k-means
        self.centroids[id] = self.evaluate_ind_kmeans(results) 
        return self.centroids[id]  

    #Evaluating k-means at global level (i.e. considering all matrices of all the users)
    #iterate over different values of k and find the best one
    def evaluate_global_kmeans(self):
        sse_list = list()
        total_list = numpy.zeros(shape=(1, 28))
        for customer in self.centroids.keys():
            total_list = numpy.concatenate((total_list, self.centroids[customer]), axis=0)
        total_list = numpy.delete(total_list, (0), axis=0)   
        for k in range (1, len(total_list)):
            kmeans = KMeans(n_clusters=k)
            kmeans.fit(total_list)
            sse_list.append(kmeans.inertia_) 
        k = self.get_knee_point_value(sse_list)  
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(total_list)
        return kmeans    

    #Evaluating k-means at individual level
    #iterate over different values of k and find the best one
    def evaluate_ind_kmeans(self, results):
        sse_list = list()
        for k in range(1, len(results)):
            kmeans = KMeans(n_clusters=k)
            kmeans.fit(results)
            sse_list.append(kmeans.inertia_)
        #case of zero matrices, keep the number of them for future needs   
        if len(sse_list) == 1:
            if sse_list[0] == float(0):
                return numpy.zeros(shape=(1, 28))        
        k = self.get_knee_point_value(sse_list)  
        if k == 0:
            k = 1 
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(results)
        #check for clients with less than 3 purchases
        if len(kmeans.cluster_centers_) > 28:
            print kmeans.cluster_centers_
        return kmeans.cluster_centers_

    #This function creates the structure for the individual profile creation
    def create_matrices(self, customer_id, start, end):
        index_week = 1
        self.matrices[customer_id] = dict()
        self.matrices[customer_id][index_week] = list()
        keys = list()      
        keys = self.customers[customer_id].keys()
        keys = sorted(keys)
        keys_date = list()
        for key in keys:
            keys_date.append(key.date())
        index_days = start.weekday() 
        if index_days != 0:    
            for i in range (0, 5):
                self.matrices[customer_id][index_week].append([0, 0, 0, 0, 0, 0, 0])     
        for day in pd.date_range(start, end):
            if index_days == 0:
                index_week += 1
                self.matrices[customer_id][index_week] = list()
                for i in range(0, 5):
                    self.matrices[customer_id][index_week].append([0, 0, 0, 0, 0, 0, 0])  
            if day.date() in keys_date:
                for k in keys:
                    if day.date() == k.date():
                        self.iter(k, index_days, index_week, customer_id)
                        break
            index_days = (index_days + 1) % 7
        return index_week    

    #This function puts in the right cell the value returned from the function relevance       
    def iter(self, day, index_days, index_week, customer_id):
        self.matrices[customer_id][index_week][0][index_days] = day.date()
        items = self.relevance(customer_id)
        hour = day.hour
        if hour < 11:
            self.matrices[customer_id][index_week][1][index_days] = items
        elif hour < 15:
            self.matrices[customer_id][index_week][2][index_days] = items
        elif hour < 18:    
            self.matrices[customer_id][index_week][3][index_days] = items 
        else:
            self.matrices[customer_id][index_week][4][index_days] = items 

    #This function evaluates the relevance of the purchase        
    def relevance(self, customer_id):
        shop_id = self.customers[customer_id][day].keys()
        return len(self.customers[customer_id][day][shop_id[0]].keys())

    #This function handles the different structures needed for k-means evaluation
    def conform_data_kmeans(self, id, index_week):
        results = numpy.zeros(shape=(1, 28))
        used = False
        for i in range (1, index_week):
            for row in range(1, 4):
                for el in range(0, 6):
                    if self.matrices[id][i][row][el] != 0 :
                        if used == False:
                            res = numpy.zeros(shape=(1,28))
                            used = True
                        value  = self.matrices[id][i][row][el]
                        pos = (row -1 )*7+el
                        res[0][pos] = value
            if used:
                results = numpy.concatenate((results, res), axis=0) 
            else:    
                self.count_zero_matrices += 1
        results = numpy.delete(results, (0), axis=0)
        return results

    # This function discovers the best value for the parameter k in k-means
    # values is a list of sse values
    def get_knee_point_value(self, values):
        y = values
        x = np.arange(0, len(y))

        index = 0
        max_d = -float('infinity')

        for i in range(0, len(x)):
            c = self.closest_point_on_segment(a=[x[0], y[0]], b=[x[-1], y[-1]],p=[x[i], y[i]])
            d = np.sqrt((c[0] - x[i])**2 + (c[1] - y[i])**2)
            if d > max_d:
                max_d = d
                index = i              
        return index

    # This function returns the closest point to the knee of the curve
    def closest_point_on_segment(self, a, b, p):
        sx1 = a[0]
        sx2 = b[0]
        sy1 = a[1]
        sy2 = b[1]
        px = p[0]
        py = p[1]

        x_delta = sx2 - sx1
        y_delta = sy2 - sy1

        if x_delta == 0 and y_delta == 0:
            return p

        u = ((px - sx1) * x_delta + (py - sy1) * y_delta) / (x_delta * x_delta + y_delta * y_delta)

        cp_x = sx1 + u * x_delta
        cp_y = sy1 + u * y_delta
        closest_point = [cp_x, cp_y]

        return closest_point         