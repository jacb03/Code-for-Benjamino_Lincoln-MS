import matplotlib as ml
ml.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import os
import cPickle as pickle
from numpy import log2


class Heatmap:
    """
    Creates heatmap object based on heatmap array generated
    """
    
    def __init__(self, heatmap):
        self.heatmap = heatmap
        self.heatmap_trans = zip(*heatmap)
    
    def get_row_avgs(self):
        avgs = []
        for a in self.heatmap:
            abs_array = np.absolute(a)
            avg = np.average(abs_array)
            avgs.append(avg)
        self.row_avgs = avgs

    def get_col_avgs(self):
        avgs = []
        for a in self.heatmap_trans:
            abs_array = np.absolute(a)
            avg = np.average(abs_array)
            avgs.append(avg)
        self.col_avgs = avgs


def create_heat_map(ann, inputs, names, bias=False, save_path=None, percent=0.05, scaling=False):
    '''
    Creates a senstivity heatmap given inputs (array)
    Bias asssumes first entry in dataset is the bias node. Will not run analysis on first entry
    and skip plotting it as well - defaults to True
    '''
    #Initialize stuff
    inputs = [float(i) if i != 0 else float(0.000001) for i in inputs]
    inputs[-6] = 0.01
    inputs[-5] = 0.01
    inputs[-4] = 0.01
    inputs[-3] = 0.01
    inputs[-2] = 0.01
    inputs[-1] = 0.01
    heat_array = []
    zeros = [0]*ann.get_num_input()
    averages = []
    base_outputs = [float(i) for i in ann.run(inputs)]
 
    if bias == True:
        node_start = 1
    else:
        node_start = 0
    
    # Determine relative changes by changing each input nodes one at a time
    # To series of values, then see how output changes relative to each input
    for i in range(node_start, len(inputs)):
        changes = []
        if (inputs[i] == 0) and (i < (int(len(inputs))-6)): #If the input node equals 0 and not food
            input_range = np.linspace(0.00001, 0.0001, 100)
        elif (inputs[i] == 0) and (i >= (int(len(inputs))-6)): # elseif its 0 and food
            input_range = np.linspace(0.0001, 0.01, 100)
        else:
            input_range = np.linspace(inputs[i], (1+percent)*inputs[i], 100)

        counter = 0.0
        
        for j in input_range:
            new_inputs = inputs[:]  #Reset to original
            if j == inputs[i]:
                j = j*1.01
            new_inputs[i] = float(j) #change to new input node value
            new_outputs = ann.run(new_inputs)   
            relative_changes = []
            for index,value in enumerate(new_outputs):
                if base_outputs[index] != 0 and value > 0.001:
                    relative_changes.append(((value-base_outputs[index])/base_outputs[index]) / ((new_inputs[i] - inputs[i]) / inputs[i]))
                elif base_outputs[index] == 0 and value > 0.001:
                    relative_changes.append(value / ((new_inputs[i] - inputs[i]) / inputs[i]))
                else:
                    relative_changes.append(0)
            changes.append(relative_changes)
            counter += 1.0
        heat_array.append(np.divide(np.sum(changes, axis=0), counter)) #Sum over columns, divide to get average change, add to heat array
    
    for row_num, rval in enumerate(heat_array):
        for col_num, cval in enumerate(rval):
            if row_num == col_num: heat_array[row_num][col_num] = 0
    heat_array = np.array(np.tanh(heat_array))
    #scaling
    if scaling == True:
        heat_array_mat = np.matrix(heat_array)
        avg = heat_array_mat.mean()
        std = heat_array_mat.std()
        for ind, row in enumerate(heat_array):
            heat_array[ind] = np.tanh((row - avg) / std)
    
    
    column_labels = [i for i in (range(node_start, ann.get_num_output()+1))]
    row_labels = [i for i in (range(node_start, ann.get_num_input()))]
    

    # Plot with matplotlib

    fig, ax = plt.subplots()
    heatmap = ax.pcolor(heat_array, cmap=plt.cm.RdBu, vmin=-1, vmax=1)
    fig.set_size_inches(18.5,18.53)
    fig.set_dpi(600)
    #Set legend
    cbar = plt.colorbar(heatmap)
    cbar.ax.get_yaxis().set_ticks([])
    for j, lab in enumerate(['Strong Inverse', 'Slight Inverse', 'No Relation','Slight Direct', 'Strong Direct']):
        cbar.ax.text(0.5, (2 * j + 1) / 10.0, lab, ha='center', va='center',fontsize=16)
    cbar.ax.get_yaxis().labelpad = 0
    cbar.ax.set_ylabel('Relationship Direction and Strength', rotation=270, labelpad=45, fontsize=16)
    # put the major ticks at the middle of each cell
    ax.set_xticks(np.arange(heat_array.shape[1])+0.5, minor=False)
    ax.set_yticks(np.arange(heat_array.shape[0])+0.5, minor=False)
    ax.set_xlim([0,int(ann.get_num_output())])
    ax.set_ylim([0,int(ann.get_num_input())])
    # want a more natural, table-like display
    ax.invert_yaxis()
    ax.xaxis.tick_top()

    #rotate x axis 90 degrees
    plt.xticks(rotation=90)

    #set font
    ax.set_xticklabels(column_labels, minor=False)
    ax.set_yticklabels(row_labels, minor=False)
    ax.xaxis.set_tick_params(labelsize=10)
    ax.yaxis.set_tick_params(labelsize=0)
    ax.yaxis.set_ticks_position('none') 
    #Show it
    #plt.show()
    file_name = "heatmap.tiff"
    plt.tight_layout()  
    # Save as pdf
    if save_path != None:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        save_path = os.path.join(save_path, file_name)
        #pdf = PdfPages(save_path)
        plt.close()
        fig.savefig(save_path)
        #pdf.close()
    return heat_array


def save_heatmap_array(heatmap_array, save_name):
    '''
    Saves the array in pickle format for easier analysis later with graph-tools and such, so we dont have to generate it every time we want to test some new analysis methods
    '''
    
    dir = os.path.dirname(__file__)
    filename = os.path.join(dir, '../../data/heatmaps/{0}'.format(save_name))
    pickle.dump(heatmap_array, open(filename, "wb" ))
