from pyfann import libfann as lf
import csv
import sys
import os
from pprint import pprint as pr
#++++++++++     
basedir = os.path.dirname(__file__)
clib = '../lib/python/'
sys.path.append(os.path.join(basedir, clib))
#++++++++++
import heatmap_generator as hmg
import analysis as an
import cPickle as pickle
import numpy as np
import csv
import data_parser

global names_location, save_path, inputs_location, test_location
save_path = "../figures/order_all_averaged_fixed/"
names_location = "../data/names/order_all_averaged_fixed.txt"
net_location = "../data/networks/best.net"
inputs_location = "../data/Fixed Dataset/Validation/validation.csv"
test_location = "../data/Fixed Dataset/Averaged/Test/"
def create_and_save(scaling=False):
    '''
    Creates and saves a heatmap if sys.argv[1] = create
    '''


    # Load the saved neural net
    ann = lf.neural_net()
    ann.create_from_file(net_location)

    # Get the names, put into array
    names_list = [line.rstrip('\n') for line in open(names_location)]
    #print names_list
    # Get inputs to create heat array with
    with open(inputs_location) as f:
        inputs_csv = csv.reader(f, delimiter=',')
        inputs = [float(i) for i in inputs_csv.next()]
    
    #Create
    heatmap = hmg.create_heat_map(ann, inputs, names_list, bias=False, save_path=save_path, scaling = False)
    
    #Save
    hmg.save_heatmap_array(heatmap, "order.p")

    return heatmap

"""
def create_and_save(scaling=False):
    '''
    Creates and saves a heatmap if sys.argv[1] = create
    '''

    # Load the saved neural net
    ann = lf.neural_net()
    ann.create_from_file(net_location)

    # Get the names, put into array
    names_list = [line.rstrip('\n') for line in open(names_location)]

    inputs_array = []
    # Get inputs to create heat array with
    with open(inputs_location) as f:
        inputs_csv = csv.reader(f, delimiter=',')
        for inputs in inputs_csv:
            inputs = [float(i) for i in inputs]
            inputs_array.append(inputs) 
    #Create
    heatmap = hmg.create_heat_map(ann, inputs_array, names_list, bias=False, save_path="../figures/order/", scaling = False)
    
    #Save
    hmg.save_heatmap_array(heatmap, "order.p")

    return heatmap
"""

def main():

    # Get heatmap from creation or loading
    ann = lf.neural_net()
    ann.create_from_file(net_location)

    # Replace this nonsense with argparse later on
    # But for now, we live in anarchy
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'create':
        heatmap = create_and_save(scaling=False)
    elif len(sys.argv) > 1 and sys.argv[1].lower() == 'load':   #load from file
        heatmap = pickle.load(open(os.path.join(basedir, '../data/heatmaps/order.p'),'rb'))
    else:
        print "Please input a valid argument to {0}, either `create` or `load`".format(sys.argv[0])
        sys.exit(1)
    
    Heatmap = hmg.Heatmap(heatmap)
    Heatmap.get_row_avgs()
    Heatmap.get_col_avgs()


    # Need for loop here
 
    
    names_list = [line.rstrip('\n') for line in open(names_location)]
    names_dict = {}     # key=name, value=index
    for i,v in enumerate(names_list):
        names_dict[v] = str(i)
    rmse, bray_curtis = an.test_network(ann, test_location, save_path)
    # Now we have the heatmap object so lets do some stuff
    g = an.create_fuzzy_hairball(Heatmap, save_path) 
    #out_dict = an.get_out_degrees(g, names_list)
    #pr(out_dict)
    print "\n"
    #in_dict = an.get_in_degrees(g, names_list)
    #pr(in_dict)
    
    # These are ordered dicts, with least connectected first (ascending order)
    
    # Create heatmap value csv

    heatmap_csv = csv.writer(open("heatmap_values.csv", 'w'), delimiter=',')
    heatmap_csv.writerow([""]+names_list[0:-6])
    for i,v  in enumerate(Heatmap.heatmap):
        heatmap_csv.writerow([names_list[i]] + [str(s) for s in v])
    



    in_degree_dict = an.get_degrees(g, names_list, "in")
    out_degree_dict = an.get_degrees(g, names_list, "out")
    total_degree_dict = an.get_degrees(g, names_list, "all")
    
    with open('degrees.csv', 'w') as degree_csv_filehandle:
        degree_csv = csv.writer(degree_csv_filehandle)
        degree_csv.writerow(['Taxon', 'In', 'Out', 'Total'])
        for k in total_degree_dict.keys():
            ins = str(in_degree_dict[k])
            outs = str(out_degree_dict[k])
            total = str(total_degree_dict[k])
            degree_csv.writerow([k, ins, outs, total])

    old_total = pickle.load( open( "total_degree_dict_orig.p", "rb" ) )

    for d in total_degree_dict.keys():
        if d in old_total.keys():
            print "{0}:\t{1} {2}\t| {3}".format(d, old_total[d], total_degree_dict[d], np.absolute(old_total[d] - total_degree_dict[d]))
    
    old_top_ten = ['Leptospirales', 'Methylacidiphilales', 'Methanobacteriales', 'Coriobacteriales', 'Clostridiales', 'Bacteroidales', 'Fusobacteriales', 'Rhodocyclales', 'Spirochaetales']
 
    top_ten = an.create_topten_bar(total_degree_dict, save_path, names_dict)
    print old_top_ten
    print top_ten
    #pwr_file = open(save_path + "power_stuff.csv", 'w')
    #csv_writer = csv.writer(pwr_file, delimiter=',')
    #csv_writer.writerow(["Number", "Name", "In Degrees", "Out Degrees", "Total Degrees"])
    g = an.create_fuzzy_hairball_fixed(Heatmap, save_path, 10, total_degree_dict, names_list)
    counter = 0
    #for name in names_list:
    #    csv_writer.writerow([counter, name, in_degree_dict[name], out_degree_dict[name], total_degree_dict[name]])
    #    counter += 1
    #pwr_file.close()
    

    np.set_printoptions(precision=4)
    print len(in_degree_dict)
    print rmse
    print bray_curtis

    
if __name__ == "__main__":
    main()
