# generic functions for data preprocessing (1D, 2D, 3D, 4D, etc.)
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
import glob
import pickle
import cv2
import time
from natsort import natsorted
#import detectron2 # 
print('Tibbling AI - Preprocess Framework Activated')
        
def ordered_files(path):
  os.chdir(path)
  print('loading folder in process')
  ordered = []
  for fname in natsorted(glob.glob('**')):
    ordered.append(fname)
  return ordered
 
def load_pickle(filename):
  with open(filename, 'rb') as handle:
    temp = pickle.load(handle)
  return temp
   
def save_pickle(filename,dict_file):
   with open(filename, 'wb') as handle:
      pickle.dump(dict_file, handle, protocol=pickle.HIGHEST_PROTOCOL)

def time_calculate(start=None):
   # input:  bool start Tru
   # output: end time
   # todo: replace with a wrapper function?
   if start==None:
      return time.time()
   else:
      end = (time.time() - start) # secs
      if end<60:
        print('seconds: ',end)
        return end
      else:
        end = ((time.time() - start))/60 # minutes
        print('minutes: ',end)
        return end 

def plotting_grid(num_images=36):
    plt.figure(figsize = (6,6))
    gs1 = gridspec.GridSpec(6, 6)
    gs1.update(wspace=0.025, hspace=0.05) # set the spacing between axes. 
    for sect_id in range(num_images):
        ax1 = plt.subplot(gs1[sect_id])
        ax1.set_xticklabels([])
        ax1.set_yticklabels([])
        ax1.set_aspect('equal')