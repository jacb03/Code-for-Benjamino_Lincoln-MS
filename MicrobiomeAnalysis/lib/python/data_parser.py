#!~/anaconda/bin/python

'''
Library to take in *.csv files from a given directory and create a .data file that FANN can
train with. Note, this assumes that each csv file in directory have the same microorganisms in the same order. 
Otherwise, you done goofed and its not my fault.
'''

# Imports
import sys
import csv
import os
import numpy as np

def create_data_file(directory, data_file_name, name_file_name, bias=True, scaling = False):
    '''
    Creates .data file for training ANN
    Takes CSV's from directory and creates the data file
    CSV has the format:
    row1: Name, 0, 1, 2, 3, 4
    row2: species1, 0.231, 0.1231, 0.123.....
    row3: species2, 0.01, 0.23, 0.122......etc

    where the first row is headers, and the first column is names of species
    the subsequent columns are the abundance of species
    
    Data file is formatted as such:
    number_inputs number_outputs number_training_points
    input1
    output1
    input2
    output2

    where ins and outs are space delimited floats
    this will also output a name file of the names of each microorganism
    '''

    #Constants/Initialize
    num_food_sources = 6    
    global name_array
    name_array = []
    ####################

    
    try:
        data_file = open(data_file_name, 'w')
    except:
        print "Ooops. Either that directory you want the data to go in doesn't exist, or you don't have access to it!"
        sys.exit(1)
    
    dataset_count = 0
    
    # If there's a bias node, dont include it in output
    # This is because we don't include bias as part of the ANN output
    # Only microorganisms
    if bias == True:
        out_start = 1
    else:
        out_start = 0
    
    # Loop through directory to get csv's
    for fn in os.listdir(directory):
        counter = 0
        try:
            f = open(os.path.join(directory, fn))
        except:
            print "Now you've gone and done it. These csv's don't exist."
            sys.exit(1)
        
        csv_reader = csv.reader(f, delimiter=',')
        
        # File is now open as a csv object, get data
        # Skip headers
        next(csv_reader, None)
        row_count = 0
        data_array = []
        
        # Loop through each row in the csv file
        for row in csv_reader:
            row_count += 1
            if dataset_count == 0:
                name_array.append(row[0])
            counter += 1
            values = row[1:]                #0 is names
            
            #Scale if needed
            if scaling == True:
                values = scale_row(values)
            num_cols = len(values)  
            data_array.append(values)
        
        dataset_count = dataset_count + (num_cols - 1)  #-1 because the last timeperiod doesn't have a target
        
        f.close()
        data_array = zip(*data_array)       #Transpose so that each column is a species
                                            #Need it this way for .data file so that each row is each species at a time period for training on next time point
        i = 0
        #Again, last time period doesnt have target. Write input \n output
        while i < num_cols - 1:
            line = data_array[i]    #Input
            data_file.write('\n')
            data_file.write(' '.join(str(n) for n in line))
            line = data_array[i+1]  # Output/target
            # Food sources is in input but not output, disregard last num_food_sources
            # This is where out_start comes in from bias, since we don't want to include it as an output/target
            line = line[out_start:len(line) - num_food_sources]
            data_file.write('\n')
            data_file.write(' '.join(str(n) for n in line))
            i += 1
    
    data_file.close()
    
    # Theres probably a better way but I need to append the dataset count, inputs, and outputs to the top
    data_file = open(data_file_name, 'r')
    data = data_file.read()
    data_file.close()
    
    #Number of inputs and outputs
    num_inputs = row_count

    if bias == True:
        num_outputs = row_count - (num_food_sources + 1)        #exclude bias
    else:
        num_outputs = row_count - num_food_sources
    
    # Write total training points (dataset_count), number of inputs and outputs at top of data file
    data_file = open(data_file_name, 'w')
    data_file.write("%s %s %s" % (dataset_count, num_inputs, num_outputs))
    data_file.write(data)
    data_file.close()

    # Remember the name array? Yea let's write that to a file
    name_file = open(name_file_name, 'w')
    for name in name_array:
        print >> name_file, str(name)
    name_file.close()

def scale_row(row):
    row = [float(x) for x in row]
    stdev = np.std(np.array(row))
    mean = np.average(np.array(row))
    for ind, val in enumerate(row):
        if stdev != 0:
            row[ind] = (val - mean) / stdev
        else:
            row[ind] = (val - mean) / 1
    return row
