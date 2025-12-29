import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import ants
import numpy as np
import cv2
from TibblingAI.tibbling_preprocess import *
from TibblingAI.tibbling_RegAI import *
from TibblingAI.tibbling_SegAI import *

starq_colors = pd.read_csv('StARQ_Atlas_Image_Mappings - Cornell2Allen_FINAL_Color_Codes.csv')
starq_colors = starq_colors.dropna() #drop all nan rows
starq_colors = starq_colors.dropna(subset=['Sub-region']).loc[starq_colors['Sub-region'] != 'thalamus'].loc[starq_colors['Sub-region'] != 'Hypothalamus']

print(starq_colors.head())

mouse_label_dict = {}
for counter in starq_colors.index:
    mouse_label_dict[starq_colors['Label'][counter]] = [[int(starq_colors['R_C'][counter]),
                                                        int(starq_colors['G_C'][counter]),
                                                        int(starq_colors['B_C'][counter])]]
def alignment_model(img_channel, slice_, p_name = './processed_pickles', file_name = 'sample.tif', atlas_path = 'Atlas_Brains', template_path = 'Atlas_Brains' ):
  os.makedirs(p_name, exist_ok = True)
  if slice_ == None:
    slice_ = 'A1_S1_slice'
  print("registration::", img_channel, slice_)
  fldr, slice_num, _ = slice_.split("_")
  template_section_path = f'{template_path}/{fldr}/{slice_num.lower()}/{slice_}.png'
  # f'{atlases_dir}/{fldr}/{slice_num}/{slice_}.png'
  label_name = slice_.replace('slice', 'labels')
  template_atlas_path = f'{atlas_path}/{fldr}/{slice_num.lower()}/{label_name}.png'
  template_section = plt.imread(template_section_path)
  template_atlas = plt.imread(template_atlas_path)

  # img_channel = img_channel.split(" ")[1]
  # user_section =np.array(Image.open(f'{temp_dir}/channel_{img_channel}.png').convert("RGB"))
  user_section = img_channel

  template_section = fix_background(
                                                                square_padding(
                                                                gray_scale(template_section)))

  print(np.shape(user_section), np.shape(template_atlas), np.shape(template_section))
  template_atlas = (template_atlas/np.max(template_atlas))*255
  template_atlas = template_atlas[:,:,:3]/255

  #print(np.shape(template_atlas))
  user_section = fix_background(square_padding(gray_scale(user_section)))
  fixed_image = ants.from_numpy(user_section)
  region_mask,regions_mask_dict = atlas_parse(template_atlas,mouse_label_dict)
  template_atlas = square_padding(template_atlas)
  moving_atlas_ants = ants.from_numpy(1-template_atlas[:,:,0]) # dummy for testing the entire atlas
  moving_image = ants.from_numpy(template_section)
  
  mytx = affine_reg(fixed_image,moving_image)

  regist_fixed_atlas_parsed = {}
  for region in regions_mask_dict:
      affined_fixed_atlas = ants.apply_transforms(fixed=fixed_image,
                                                  moving=ants.from_numpy(regions_mask_dict[region]),
                                                  transformlist=mytx['fwdtransforms'],
                                                  interpolator='nearestNeighbor')#moving_atlas_ants
      regist_fixed_atlas_parsed[region] = affined_fixed_atlas.numpy()
  affined_fixed_atlas = ants.apply_transforms(fixed=fixed_image,
                                                  moving=moving_atlas_ants,
                                                  transformlist=mytx['fwdtransforms'],
                                                  interpolator='nearestNeighbor')


  mytx_non_rigid = nonrigid_reg(fixed_image,mytx,'SyN')
  for region in regions_mask_dict:
      nonrigid_fixed_atlas = ants.apply_transforms(fixed=fixed_image,
                                              moving=ants.from_numpy(regist_fixed_atlas_parsed[region]),
                                              transformlist=mytx_non_rigid['fwdtransforms'],
                                              interpolator='nearestNeighbor')
      regist_fixed_atlas_parsed[region] = nonrigid_fixed_atlas.numpy()
  nonrigid_fixed_atlas = ants.apply_transforms(fixed=fixed_image,
                                              moving=affined_fixed_atlas,
                                              transformlist=mytx_non_rigid['fwdtransforms'],
                                              interpolator='nearestNeighbor')
  plt.figure(figsize=(10,5))
  plt.subplot(1,6,1); plt.imshow(fixed_image.numpy(),cmap='inferno'); plt.title('moving')
  plt.subplot(1,6,2); plt.imshow(moving_image.numpy(),cmap='inferno'); plt.title('fixed')
  plt.subplot(1,6,3); plt.imshow(mytx_non_rigid['warpedmovout'].numpy(),cmap='inferno'); plt.title('non-rigid registered')
  plt.subplot(1,6,4); plt.imshow(fixed_image.numpy(),cmap='inferno'); plt.imshow(mytx['warpedmovout'].numpy(),alpha=0.5,cmap='viridis'); plt.title('affine - overlaid')
  plt.subplot(1,6,5); plt.imshow(fixed_image.numpy(),cmap='inferno'); plt.imshow(mytx_non_rigid['warpedmovout'].numpy(),alpha=0.5,cmap='viridis'); plt.title('after non-rigid - overlaid')
  plt.subplot(1,6,6); plt.imshow(mytx_non_rigid['warpedmovout'].numpy(),cmap='gray'); plt.imshow(nonrigid_fixed_atlas.numpy(),alpha=0.5,cmap='inferno'); plt.title('after non-rigid - atlas overlaid')
  plt.tight_layout()
  plt.savefig(p_name+f'{file_name.split(".")[0]}.png', bbox_inches = 'tight')
  f_name = p_name+file_name.split('.')[0]+'.pkl'
  save_pickle(f_name,regist_fixed_atlas_parsed)

  return regist_fixed_atlas_parsed

def qualitative_result(regist_fixed_atlas_parsed, user_image, with_label = False, file_name = 'sample.tif', result_path = './Results/Qualititative_results' ):
  if not(os.path.exists(result_path)): os.makedirs(result_path)
  print("Creating Qualitative Results")
  blank_canvas = np.zeros(user_image.shape)

  temp_contours_global = []
  temp_contours_global_color = []
  temp_mask_centers = {}
  temp_box_corners = {}
  global_temp_white = np.zeros((256,256,4))
#   f_name = p_name+file_name.split('.')[0]+'.pkl'
  temp_pkl = regist_fixed_atlas_parsed #load_pickle(f_name)
  print("Extracting colors!!!")
  for key in temp_pkl:
        #plt.subplot(grid,grid,count+1);
        temp_white = np.zeros((256,256,4))
        temp = temp_pkl[key]
        kernel = np.ones((1,1),np.uint8)
        temp = cv2.dilate((temp_pkl[key]), kernel, iterations = 10)
        for x in range(3):
            temp_white[:,:,x] = (temp)*mouse_label_dict[key][0][x]/255
        temp_white[:,:,3] = temp
        global_temp_white+=temp_white
        full_white = np.zeros((256,256,3))
        contours, hierarchy = cv2.findContours(np.uint8((temp)>0), cv2.RETR_TREE,cv2.RETR_CCOMP)#, cv2.CHAIN_APPROX_SIMPLE)# cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)#cv2.RETR_TREE
        temp_contours_global.append(contours)
        temp_contours_global_color.append([mouse_label_dict[key][0][0]/255,mouse_label_dict[key][0][1]/255,mouse_label_dict[key][0][2]/255])
        if np.sum(temp_pkl[key])>0:
                center_x, center_y = get_center_of_mask(np.uint8((temp)>0))#((temp_pkl[key]>0))
                temp_mask_centers[key] = [[center_x,center_y],[mouse_label_dict[key][0][0]/255,mouse_label_dict[key][0][1]/255,mouse_label_dict[key][0][2]/255]]
                binary_mask = temp_pkl[key]
                # bounding box
                min_x, min_y, max_x, max_y = get_bounding_box(np.uint8((temp)>0))#((temp_pkl[key]))
                temp_box_corners[key] = [[min_x, min_y, max_x, max_y],[mouse_label_dict[key][0][0]/255,mouse_label_dict[key][0][1]/255,mouse_label_dict[key][0][2]/255]]

  fig, ax = plt.subplots()

  ax.imshow(user_image,cmap='gray',extent=[0, 256, 0, 256]);
  if with_label:
    print("Adding Text")

    for key in temp_box_corners:
            [min_x, min_y, max_x, max_y] = temp_box_corners[key][0]
            plt.gca().add_patch(plt.Rectangle((min_x, min_y), max_x - min_x, max_y - min_y,
                                      edgecolor=temp_box_corners[key][1], facecolor='none', lw=2 ,linestyle='-'))

            # Add text label 'reg' in the top-left corner of the bounding box
            plt.text(min_x, max_y, key, color=temp_box_corners[key][1], fontsize=12,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(facecolor='white', alpha=0.3, edgecolor='none'))
  color_count = 0
  for contours in temp_contours_global:
      for contour in contours:
          path_data = []
          for point in contour:
              x, y = point[0]
              x, y = x,256-y
              #x, y = x-256,y
              path_data.append((Path.LINETO, (x, y)))
          path_data.append((Path.LINETO, (contour[0][0][0], 256 - contour[0][0][1])))
          path_data[0] = (Path.MOVETO, path_data[0][1])  # Change the first point to MOVETO

          # Create a Path object and patch
          codes, verts = zip(*path_data)
          path = Path(verts, codes)
          patch = PathPatch(path, facecolor='none', edgecolor=temp_contours_global_color[color_count], lw=1)
          # Add patch to the plot
          ax.add_patch(patch)
      color_count+=1

  ax.set_xlim(0, 256)
  ax.set_ylim(0, 256)
  ax.axis('off')
  final_save_path = f'{result_path}/{file_name.split(".")[0]}_contours.svg'
  if with_label:
    final_save_path = final_save_path.replace(".svg", "_with_labels.svg")
  plt.savefig(final_save_path, bbox_inches = 'tight')
  plt.savefig(final_save_path.replace('.svg', '.png'), bbox_inches = 'tight')

  return final_save_path.replace('.svg', '.png')




def signal_quantification(signal_channels, p_name, temp_dir, file_name ='sample.tif', result_path = './Results/Quantitative_results/'):
  if not(os.path.exists(result_path)): os.makedirs(result_path)
  os.makedirs(f'{result_path}/Signal_Raw/', exist_ok = True)
  os.makedirs(f'{result_path}/Area/', exist_ok = True)
  os.makedirs(f'{result_path}/Signal/', exist_ok = True)


  f_name = p_name+file_name.split('.')[0]+'.pkl'
  print(f_name)
  temp = load_pickle(f_name)
  sig_channels = [int(ch.split("Channel ")[-1]) for ch in signal_channels]
  print("Signal Channels::", signal_channels, sig_channels, len(list(temp.keys())))
  channel_wise_dict = load_pickle(f'{temp_dir}/{file_name}_original.pkl')
  dict_fname = file_name.split(".")[0]
  for ch_num in sig_channels:
    ch0 = channel_wise_dict[ch_num]
    print(ch0)
    M1S1c_F1_signal_quant_ch0 = {}
    M1S1c_F1_signal_quant_ch0[dict_fname] = {}
    for key in temp:
          if np.sum(temp[key])>0 and (np.sum(temp[key]*ch0)/np.sum(temp[key]))>0:#0.0001  (np.sum(temp[key]*ch1)/np.sum(temp[key]))<0.0001 and
              M1S1c_F1_signal_quant_ch0[dict_fname][key] = np.sum(temp[key]*ch0)#/np.sum(temp[key])
          else:
              M1S1c_F1_signal_quant_ch0[dict_fname][key] = 'na'
    M1S1c_F1_signal_quant_ch0_csv = pd.DataFrame.from_dict(M1S1c_F1_signal_quant_ch0)
    M1S1c_F1_signal_quant_ch0_csv.head()
    M1S1c_F1_signal_quant_ch0_csv.to_csv(result_path+'Signal_Raw/'+f'{file_name.split(".")[0]}_signal_quant_ch{ch_num}_signal_raw_csv.csv') #, sep='\t', encoding='utf-8')


    M1S1c_F1_signal_quant_ch0 = {}
    M1S1c_F1_signal_quant_ch0[dict_fname] = {}
    for key in temp:
        if np.sum(temp[key])>0  and (np.sum(temp[key]*ch0)/np.sum(temp[key]))>0:#0.0001  (np.sum(temp[key]*ch1)/np.sum(temp[key]))<0.0001 and
            M1S1c_F1_signal_quant_ch0[dict_fname][key] = np.sum(temp[key])#np.sum(temp[key]*ch0)#/np.sum(temp[key])
        else:
            M1S1c_F1_signal_quant_ch0[dict_fname][key] = 'na'



    M1S1c_F1_signal_quant_ch0_csv = pd.DataFrame.from_dict(M1S1c_F1_signal_quant_ch0)
    M1S1c_F1_signal_quant_ch0_csv.head()
    M1S1c_F1_signal_quant_ch0_csv.to_csv(result_path+'Area/'+f'{file_name.split(".")[0]}_signal_quant_ch{ch_num}_signal_raw_csv.csv') #, sep='\t', encoding='utf-8')


    M1S1c_F1_signal_quant_ch0 = {}
    M1S1c_F1_signal_quant_ch0[dict_fname] = {}
    for key in temp:
        if np.sum(temp[key])>0 and (np.sum(temp[key]*ch0)/np.sum(temp[key]))>0:#0.0001  (np.sum(temp[key]*ch1)/np.sum(temp[key]))<0.0001 and
            M1S1c_F1_signal_quant_ch0[dict_fname][key] = np.sum(temp[key]*ch0)/np.sum(temp[key])
        else:
            M1S1c_F1_signal_quant_ch0[dict_fname][key] = 'na'



    M1S1c_F1_signal_quant_ch0_csv = pd.DataFrame.from_dict(M1S1c_F1_signal_quant_ch0)
    M1S1c_F1_signal_quant_ch0_csv.head()
    M1S1c_F1_signal_quant_ch0_csv.to_csv(result_path+'Signal/'+f'{file_name.split(".")[0]}_signal_quant_ch{ch_num}_signal_raw_csv.csv') #, sep='\t', encoding='utf-8')
    

  # return gr.update(value = f"Results saved successfully at {result_path}", visible = True)

