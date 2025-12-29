# generic functions for RegAI product (registration of biological atlas on 2D/3D imaging data)
import ants # pip install antspyx # https://pypi.org/project/antspyx/
import numpy as np
import matplotlib.pyplot as plt
import cv2
import TibblingAI
import TibblingAI.tibbling_SegAI

print('Tibbling AI - RegAI product framework activated')
# Sample:
# https://colab.research.google.com/drive/1oIa64ebgAzw1C-75qxPYlWHcwdRnZal_#scrollTo=R1CXmKETdYeC

def affine_reg(fixed_image,moving_image,gauss_param=100):
    # this function takes fixed and moving images as input and return affine transformation matrix
    # fixed/moving images can be 2D/3D
    # todo: add an option as flag to save the transformation matrix and displacement fields at the desired location to be able to apply the transforms later
    mytx = ants.registration(fixed=fixed_image, 
                         moving=moving_image, 
                         type_of_transform='Affine', 
                         reg_iterations = (gauss_param,gauss_param,gauss_param,gauss_param))
    print('affine registration completed')
    return mytx


def nonrigid_reg(fixed_image,mytx,type_of_transform='SyN',grad_step=0.25,reg_iterations=(50,50,50, ),flow_sigma=9,total_sigma=0.2):
    # this function takes fixed image and affined tx matrix as input and return non-rigid transformation matrix
    # fixed/moving images can be 2D/3D
    # type of transform selection: https://antspy.readthedocs.io/en/latest/registration.html
    # todo: scale the function to incorporate the extended parameters for type_of_transform
    # todo: scale the function to incorporate the affine+non-rigid simultaneously in case of SyNRA

    transform_type = {'SyN':{'grad_step':grad_step,'reg_iterations':reg_iterations,'flow_sigma':flow_sigma,'total_sigma':total_sigma},
                      'SyNRA':{'grad_step':grad_step,'reg_iterations':reg_iterations,'flow_sigma':flow_sigma,'total_sigma':total_sigma}}
    
    mytx_non_rigid = ants.registration(fixed = fixed_image,
                                   moving=mytx['warpedmovout'], 
                                   type_of_transform=type_of_transform,
                                   grad_step=transform_type[type_of_transform]['grad_step'], 
                                   reg_iterations=transform_type[type_of_transform]['reg_iterations'],
                                   flow_sigma=transform_type[type_of_transform]['flow_sigma'],
                                   total_sigma=transform_type[type_of_transform]['total_sigma'])
    
    print('non-rigid registration completed')
    return mytx_non_rigid

def specie_classifer():
    # input: a 2D brain section of mouse/human
    # output: a clasiffication score of each category
    return True

def image_axis_classifer():
    # input: a 2D brain section of mouse/human brain
    # output: axis classification (e.g. sagittal, coronal, horizontal)
    # example: should be called right after specie classifer()
    # todo: potentially use the samples from here:
        # coronal:    https://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/slice_images/coronal/
        # sagittal:   https://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/slice_images/sagittal/
        # horizontal: https://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/slice_images/horizontal/
    return True

def atlas_image_search():
    # input: a moving 2D image drawn from mouse/human brain
    # output: a corresponding 2D image from mouse/human atlas with its atlas segmentation
    # Example: Can you apply (word2vec(registration/mapping/align)) (affine_reg+nonrigid_reg) of brain_image_21 (moving_image) on the standard atlas (atlas_image_search(moving_image))?
    # exmaple: usually called after specie_classifer() and image_axis_classifer()
    # todo: build a class of RegAI that will create the relevant objects and call functions in order
    return True

def atlas_parse(mask_temp,mouse_label_dict):
    # input:  atlas (color-coded) high-res image (mask_temp - must be high-res), mouse_label_dict contains regions as keys and color labels [R,G,B] as values
    # output: individual masks of each color-coded region
    # todo: atm function accepts RGB image as input, make it generalise to accept grayscale image
    # todo: atm function resize the masks to 256x256, make it generalise so user can select the downsizing flag
    # todo: if the mask_temp image is low res then consider relaxing the min_thr and max_thr
    # todo: consider not returning the absent binary mask labels
    # todo: make it generalise so a grayscale (mask_temp) can also be incorporated or a new function for dedicated mouse atlas
    # relevant: https://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/annotation/
    region_masks_dict = {}
    counter=1
    region_mask = np.zeros((256,256))
    for key in mouse_label_dict:
        #region_mask = np.zeros((256,256))#np.zeros(np.shape(mask_temp)[:2])
        count = 1
        region = key
        #plt.figure(figsize=(10,5))
        #plt.subplot(1,len(mouse_label_dict[region])+2,count); plt.imshow(TibblingAI.tibbling_SegAI.square_padding(mask_temp)); #plt.title(A4_masks_mapped[x].split('/')[-1])
        count+=1
        # skip the codes for loop since a single label may not have more than one RGB code
        for codes in mouse_label_dict[region]:
            min_thr = [codes[0],codes[1],codes[2]]; min_thr = np.array(min_thr)
            max_thr = [codes[0],codes[1],codes[2]]; max_thr = np.array(max_thr)
            single_binary = cv2.inRange(mask_temp[:,:,:3]*255,min_thr,max_thr)
            single_binary = TibblingAI.tibbling_SegAI.square_padding(single_binary)
            single_binary = np.uint8(single_binary>0) # conversion to 0 and 1
            region_masks_dict[key] = single_binary
            region_mask+=single_binary
            #plt.subplot(1,len(mouse_label_dict[region])+2,count); plt.imshow(single_binary); #plt.title(codes[0])
            count+=1
        #plt.subplot(1,len(mouse_label_dict[region])+2,count); plt.imshow(region_mask); plt.title(region)
        #plt.tight_layout()
        region_mask = np.uint8(region_mask>0) # conversion to 0 and 1
        print(key,' --- ',str(counter),'/',len(mouse_label_dict.keys()),' computed')
        counter+=1
    return region_mask,region_masks_dict

def mouse_atlas_parse(temp_atlas_2D,allen_ontology):
    # input: mask_temp,mouse_label_dict
    # output: region_masks_dict -- binary masks of all present regions
    # todo: given the location of 2D atlas, we run the color_id iterations only on the present regions: present_regions
    # todo: do not iterate over regions that are not present in the allen_atlas (as unique colors e.g. root)
    # todo: keep the parent-child hierarchy intact to return to the user all the parent and child regions via LLM call
    # todo: if the integrity of the pixels in temp_atlas_2D is not compromised then np.unique(temp_atlas_2D) must be equal to present_regions
    # [Done - testing tbd]todo: keep populating the parent regions as well by the look up table (allen_ontology)
    # example: atm we return all the present regions
    #    for color_id in allen_ontology['id']:
            # iterating over all regions in the atlas
    region_mask = np.zeros((256,256))
    region_masks_dict = {}
    counter = 1
    for color_id in allen_ontology['id']:
        label = allen_ontology[allen_ontology['id']==color_id]['name']
        temp = temp_atlas_2D.copy()
        temp[(temp_atlas_2D < color_id) | (temp_atlas_2D > color_id)] = 0
        region_masks_dict[label.values[0]] = np.uint8(TibblingAI.tibbling_SegAI.square_padding(np.uint16(temp))>0)
        region_mask+=region_masks_dict[label.values[0]]
        print(counter,'/',len(allen_ontology['id']),' --- computed')
        counter+=1
    
    # fill up the parent regions that are not present directly in detected child regions
    for reg in region_masks_dict:
        parents = allen_ontology[allen_ontology['name']==reg]['structure_id_path'].values[0]
        parents = parents.split('/')
        for parent in parents:
            if parent == '':
                pass
            else:
                parent_id = str(allen_ontology[allen_ontology['name']==reg]['id'].values[0])
                if parent==parent_id:
                    pass
                else:
                    parent_name = allen_ontology[allen_ontology['id']==int(parent)]['name'].values[0]
                    region_masks_dict[parent_name]+=region_masks_dict[reg]
                    region_masks_dict[parent_name] = np.uint8(region_masks_dict[parent_name]>0)

    # possible extension to fill up the parent regions
    region_present = []
    for key in region_masks_dict:
        if np.mean(region_masks_dict[key])>0:
            region_present.append(key); #print(key,' --- present')
    print('total present regions in the given atlas (2D/3D) section: ', len(region_present),'/',len(region_masks_dict))
    
    return region_mask,region_masks_dict


def atlas_gray2rgb(gray_image):
    # input: grayscale image with unique color labels, mapping label dictionary from gray to RGB colors
    # output: RGB representation of the atlas
    return True

def mask_boundary(rgb_image):
    # input: RGB or grayscale image 
    # output: boundary of labels in the image for nice visualizations
    # example: possible call of atlas_gray2rgb() within this function to map into RGB if input is in grayscale
    return True


def low2high(sect_padd,reqd_img_size,square_size=256):
    # input:  sect_padd: 256x256 | individual masks of each color-coded region, reqd_img_size = high res original sample
    # output: reconstructed atlas image w/o pixalation
    # todo: change the reqd_img_size to only the size instead of feeding the input image
    # todo: generate polygons of each region for overlaying purpose
    # todo: [done] remove the padding from the image, rescale to match the reqd_img_size
    if len(np.shape(reqd_img_size))>2:
      return low2highRGB(reqd_img_size[:,:,:3])
    else:
      if reqd_img_size.shape[1]>reqd_img_size.shape[0]: # width>height
        scale_percent = (square_size/reqd_img_size.shape[1])*100
      else: # width<height
        scale_percent = (square_size/reqd_img_size.shape[0])*100
      width = int(reqd_img_size.shape[1] * scale_percent / 100); height = int(reqd_img_size.shape[0] * scale_percent / 100); 
      dim = (width, height)
    
    # this is a smallar cube that fits inside 256x256
    sect_temp = cv2.resize(reqd_img_size, dim, interpolation = cv2.INTER_AREA)
    # inverse of TibblingAI.tibbling_SegAI.squared_padding()
    sect_mask = sect_padd[int((square_size-np.shape(sect_temp)[0])/2):int((square_size-np.shape(sect_temp)[0])/2)+np.shape(sect_temp)[0],
                          int((square_size-np.shape(sect_temp)[1])/2):int((square_size-np.shape(sect_temp)[1])/2)+np.shape(sect_temp)[1]]
    reqd_dim = (np.shape(reqd_img_size)[1], np.shape(reqd_img_size)[0])
    return cv2.resize(sect_mask, reqd_dim, interpolation = cv2.INTER_AREA)

def low2highRGB(single_gray,reqd_img_size,padd_status=True,padd_size=256):
    return True

def area_measure(image,region_label=None):
    # input:  2D/3D brain atlas, color label (grayscale code) of region of interest
    # output: sum of the entire area/volume of pixels
    if len(np.unique(image))>2:
        return np.sum(atlas_parse(image,region_label))
    else:
        return np.sum(image)
    
def area_converter(area,atlas_meter = '25'):
    # input:  area in number of pixels of a given regions
    # outout: mapping of area from pixels to standard length martics (u_meters) 
    return area*atlas_meter
    

def atlas_GAN(image):
    # input:  a 2D/3D brain image
    # output: an atlas like 2D/3D brain image generated from GAN if necessary
    # example: usually called before/after specie_classifier()
    return True