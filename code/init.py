from customers import *
import datetime
from entropy_model import *


def create_last_file(model1, model2):
    out_data = {}
    out_data['Customers'] = {}
    for key in model1.keys():
        out_data['Customers'][key] = {}
        out_data['Customers'][key]['Model2'] = model2[key]
        out_data['Customers'][key]['Model1'] = model1[key]
        with open('data.json', 'w') as outfile:  
            json.dump(out_data, outfile)



def main():
    cs = Customers()
    #cs = cs.read_json('../')
    start = datetime.datetime.strptime('2010-09-01',"%Y-%m-%d")
    end = datetime.datetime.strptime('2010-09-30',"%Y-%m-%d")
    model1 = cs.wrapper(start, end)
    entropy_model = EntropyModel()
    #entropy_model.read_json('../')
    model2 = entropy_model.calculate_all_entropies(start, end)
    create_last_file(model1, model2)

            


if __name__ == "__main__":
    main()
