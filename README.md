# Discovering temporal regularities in retail customers’ shopping behavior
This code is based on the paper 'Discovering temporal regularities in retail customers’ shopping behavior' (EPJ Data Science2018).
The idea is to have, for each client, a set of matrices that represent his/her general shopping behaviour, taking into consideration the days and the time in which he/she goes to the supermarket. 
In particular, each matrix is built in the following manner:  

    * Seven columns: one for each day of the week (from Monday to Sunday),
    
    * Four rows: the time of the day is divided into 4 slots: [8am - 11am), [11am - 15pm), [15pm - 18pm), [18pm - 21pm), 
   
    * For each shopping session of the customer, in the correspondent cell is stored the number of items he/she bought. 
    
Given the set of all the individual matrices of a client, in order to understand the general behaviour, a k-means algorithm is applied. 
In this way, for each client there is a small set of matrices that characterise him/her.
In order to get a better vision about the common behaviour of different customers, a k-means algorithm over all the individual matrices is applied: 
in doing so, for each centroid individual matrix there is also the correspondent centroid matrix of the global clustering algorithm.
