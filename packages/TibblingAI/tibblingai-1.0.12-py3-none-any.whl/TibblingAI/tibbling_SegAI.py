# generic functions for SegAI product (segmentation of biological structures in 2D/3D imaging data)
import cv2
import numpy as np
from skimage import measure
from scipy import ndimage as ndi
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from skimage.exposure import rescale_intensity, adjust_gamma
from scipy.ndimage import rotate
import matplotlib.pyplot as plt
import TibblingAI
print('Tibbling AI - SegAI product framework activated')

def square_padding(single_gray,square_size=256):
    # e.g. square_size = 256 by default
    # takes a raw image as input
    # returns a square (padded) image as output
    # input:  2D image
    # output: 2D resized padded image
    # example: StARQ brainstem sects
    if len(np.shape(single_gray))>2:
      return square_padding_RGB(single_gray[:,:,:3], square_size)
    else:
      if single_gray.shape[1]>single_gray.shape[0]: # width>height
        scale_percent = (square_size/single_gray.shape[1])*100
        print(scale_percent)
      else: # width<height
        scale_percent = (square_size/single_gray.shape[0])*100
        print(scale_percent)
      width = int(single_gray.shape[1] * scale_percent / 100); height = int(single_gray.shape[0] * scale_percent / 100); dim = (width, height)
      sect_mask = cv2.resize(single_gray, dim, interpolation = cv2.INTER_AREA)
      sect_padd = (np.ones((square_size,square_size)))*single_gray[-20,-20]#find a better solution for single_gray[100,-100]
      sect_padd[int((square_size-np.shape(sect_mask)[0])/2):int((square_size-np.shape(sect_mask)[0])/2)+np.shape(sect_mask)[0],
                  int((square_size-np.shape(sect_mask)[1])/2):int((square_size-np.shape(sect_mask)[1])/2)+np.shape(sect_mask)[1]] = sect_mask
      return sect_padd

def square_padding_RGB(single_RGB,square_size=256):
    # e.g. square_size = 256 by default
    # takes a raw image as input
    # returns a square (padded) image as output
    # input:  2D image
    # output: 2D resized padded image
    # example: BNI images, HMS data
    if single_RGB.shape[1]>single_RGB.shape[0]: # width>height
      scale_percent = (square_size/single_RGB.shape[1])*100
    else: # width<height
      scale_percent = (square_size/single_RGB.shape[0])*100
    width = int(single_RGB.shape[1] * scale_percent / 100); height = int(single_RGB.shape[0] * scale_percent / 100); dim = (width, height)
    sect_mask = cv2.resize(single_RGB, dim, interpolation = cv2.INTER_AREA)
    sect_padd = (np.ones((square_size,square_size,3)))*np.mean(single_RGB[:10,:10])
    sect_padd[int((square_size-np.shape(sect_mask)[0])/2):int((square_size-np.shape(sect_mask)[0])/2)+np.shape(sect_mask)[0],
                int((square_size-np.shape(sect_mask)[1])/2):int((square_size-np.shape(sect_mask)[1])/2)+np.shape(sect_mask)[1],:] = sect_mask
    return sect_padd

def image_rotate(input_image,rot_counter=3):
  # input:  2D image
  # output: rotated version of input image
  for x in range(rot_counter):
    input_image = np.rot90(input_image)
    
  return input_image

def color_gray(color_rgb):
  # input:  an array of RGB colors e.g. [200,100,100]
  # output: a scalar value of after conversion to grayscale
  col_gray = 0.2125 * color_rgb[0] + 0.7154 * color_rgb[1] + 0.0721 * color_rgb[2]
  return col_gray

def image_resize(image,reqd_size):
  # input:  a 2D image
  # output: resized image to the given size e.g. reqd_size = (128,172)
  return cv2.resize(image, reqd_size, interpolation = cv2.INTER_AREA)

def gray_scale(image):
  # input:  a 2D RGB image (x,y,z)
  # output: a grayscale image (x,y)
  # todo: fix the depth issue of pixels
  if len(np.shape(image))>2:
    return cv2.cvtColor(image[:,:,:3], cv2.COLOR_RGB2GRAY)
  else:
    return image

def gray2RGB(image):
  if len(np.shape(image))==2:
    print(np.shape(image))
    temp = np.zeros(np.shape(image))
    for x in range(np.shape(temp)[2]):
      temp[:,:,x] = image
    return temp
  else:
    return image


def fix_background(fixed_image):
  # input: a 2D grayscale image
  # output: a 2D image with dark background and light tissue
  # example: top to bottom: x-axis (first axis), left to right: y-axis (second axis)
  fixed_image = fixed_image/np.max(fixed_image)
  x_shape,y_shape = np.shape(fixed_image)
  corner_ratio = 0.01
  x_shape_bound = int(x_shape*corner_ratio); y_shape_bound = int(y_shape*corner_ratio)
  top_left = np.mean(fixed_image[:x_shape_bound,:y_shape_bound])
  top_right = np.mean(fixed_image[:x_shape_bound:,y_shape-y_shape_bound:])
  bottom_left = np.mean(fixed_image[x_shape-x_shape_bound:,:y_shape_bound])
  bottom_right = np.mean(fixed_image[x_shape-x_shape_bound:,y_shape-y_shape_bound:])

  if np.mean([top_left,top_right,bottom_left,bottom_right])>0.5:
    print('background fixed')
    return 1-fixed_image
  else:
    print('background unchanged')
    return fixed_image

def image_normalise(image,div_type='max'):
  # input:  a 2D image
  # output: a 2D normalised image after subtractive and divisive normalization
  # todo: fix the potential issues of division by 0/smaller value
  norm_image = (image - np.mean(image))
  if div_type == 'max':
    norm_image = norm_image/np.max(norm_image)
  elif div_type == 'std':
    norm_image = norm_image/np.std(norm_image)
    norm_image = norm_image/np.max(norm_image)
  return norm_image

def signal_area(image,mask,label=None):
  # input: a 2D image, a binary mask image with single or multiple labels, label is the color value of the required region
  # output: a 2D image with area of the labelled region masked
  return True


def extract_polygons(im):
    '''
    input: A 2D mask (grayscale) image
    output: polygons of the connected components extracted from the mask. 
    todo: automate 0.5
    todo: automate fully_connected
    '''
    contours = measure.find_contours(im, 0.1, fully_connected='low')
    polygons = []
    for obj in contours:
        polygon = []
        for contour in obj:
            polygon.append(contour[0])
            polygon.append(contour[1])
        polygons.append(polygon)
    
    return contours, polygons

def draw_polygons(img, contours):
  '''
  input: img - 2D grayscale image
  contours - polygon (list of list) - output of extract_polygons
  output: 2D image of polygons drawn
  '''
  blank = np.ones((img.shape[0],img.shape[1] ),  np.uint8)
  for con in contours:
      cv_contour = [];
      for point in con:
          intify = [int(point[1]), int(point[0])];
          cv_contour.append([intify]); 

      # convert to numpy and draw
      cv_contour = np.array(cv_contour);
      cv2.drawContours(blank, [cv_contour.astype(int)], -1, (255), -1);

  return blank


def center_pixels(channel_0,adjust=0):
    # input: binary 2D image of SegAI neuron segmentation output
    # output: binary 2D image with center of neurons is 1 and all else 0 pixel value
    thresh = cv2.threshold(np.uint8(channel_0>0), 0, 1, cv2.THRESH_BINARY)[1]
    nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
    channel_0_bin = np.zeros(np.shape(channel_0));
    for x in range(np.shape(centroids)[0]):
        channel_0_bin[int(centroids[x][1]+adjust),int(centroids[x][0]+adjust)] = 1
    return channel_0_bin

def watershed_centers(channel_0):
    # input:  watershed labelled image 2D
    # output: binary 2D image with center of neurons is 1 and all else 0 pixel value as well as centroids
    # todo: consider returning labels as well for unique neuron segment masking
    # todo: automate footprint
    image = np.uint8(channel_0>0)
    distance = ndi.distance_transform_edt(image)
    centroids = peak_local_max(distance, footprint=np.ones((5, 5)), labels=image)
    mask = np.zeros(distance.shape, dtype=bool)
    mask[tuple(centroids.T)] = True
    markers, _ = ndi.label(mask)
    labels = watershed(-distance, markers, mask=image)
    channel_0_bin = np.zeros(np.shape(channel_0))
    adjust = 0
    for x in range(np.shape(centroids)[0]):
        channel_0_bin[int(centroids[x][0]+adjust),int(centroids[x][1]+adjust)] = 1
    return np.uint8(channel_0_bin>0),centroids

def pixel2stars(channel_0,ch_color,regist_fixed_atlas_parsed_nanfree,allen_ontology,reg_name='root'):
    kernel = np.ones((5, 5), np.uint8)
    atlas_reconst = np.zeros(np.shape(regist_fixed_atlas_parsed_nanfree[reg_name]))
    atlas_reconst = regist_fixed_atlas_parsed_nanfree[reg_name] * int(allen_ontology[allen_ontology['name']==reg_name]['id'].iloc[0])
    atlas_reconst_dilate = np.zeros(np.shape(regist_fixed_atlas_parsed_nanfree[reg_name]))#np.uint8(regist_fixed_atlas_parsed_nanfree[reg_name])
    atlas_reconst_dilate = atlas_reconst_dilate+cv2.dilate(regist_fixed_atlas_parsed_nanfree[reg_name],kernel,iterations=10)
    atlas_reconst_dilate = atlas_reconst_dilate - np.uint8(atlas_reconst>0)
    atlas_reconst_dilate = atlas_reconst_dilate *  int(allen_ontology[allen_ontology['name']==reg_name]['id'].iloc[0])
    plt.imshow(np.uint16(atlas_reconst_dilate*255),cmap='inferno',alpha=1)

    x_min,x_max,y_min,y_max = 0,np.shape(regist_fixed_atlas_parsed_nanfree[reg_name])[0],0,np.shape(regist_fixed_atlas_parsed_nanfree[reg_name])[1] 
    # mask_temp = np.ones((x_max-x_min,y_max-y_min,3))*255 # fix it for zoom-in
    cells_temp = channel_0 * regist_fixed_atlas_parsed_nanfree[reg_name]
    cells_image,cells_centroids = Tibbling.tibbling_SegAI.watershed_centers(cells_temp)
    print('number of cells: ', len(cells_centroids))
    plt.imshow(np.uint16(atlas_reconst_dilate*255),cmap='inferno',alpha=1)
    for cent in cells_centroids:
        if cent[0]>=x_min and cent[0]<=x_max and cent[1]>=y_min and cent[1]<=y_max:
            plt.plot(cent[1]-y_min,cent[0]-x_min,'o',markersize = 1,color=ch_color,alpha=0.5)

def tile(img, size=256):
    # input:  2D input image, required tile size in splitting 2D input image, set to 256 as default
    # output: tiled 2D slices on input image
    padded = np.pad(img, [(0, (size - img.shape[0] % size)), (0, (size - img.shape[1] % size))])
    slices = []
    for i in range(0, padded.shape[0], size):
        row = []
        for j in range(0, padded.shape[1], size):
            row.append(padded[i:i+size, j:j+size])
        slices.append(row)
    return slices

def tile_visualize(output):
    # input: tiled 2D slices on input image
    # output: visualization of slices as 2D 
    plt.figure()
    count = 1
    for x in range(np.shape(output)[0]):
        for y in range(np.shape(output)[1]):
            plt.subplot(np.shape(output)[0],np.shape(output)[1],count)
            plt.imshow(output[x][y],vmin=np.min(output),vmax=np.max(output),cmap='inferno'); plt.axis('off')
            count+=1

def adjust_image(patch):
    # input:  tile patch
    # output: tile patch with adjusted intensity
    # todo: generalise the thresholding parameters
    try:
        thresh = np.min([patch.max() - np.sort(patch.ravel())[-5], 10])
    except:
        return patch

    patch = np.where(patch < (patch.max() - thresh), patch - np.mean(patch), patch)
    patch += np.abs(patch.min())
    patch = (patch * 255 / patch.max()).astype(np.uint8)
    patch = adjust_gamma(patch)

    v_min, v_max = np.percentile(patch, (0.1, 99.9))
    if v_max < 80:
        patch = rescale_intensity(patch, in_range=(v_min, max(v_max, 80)))

    return patch

def preprocess(img, size=256):
    # input: 2D input image, required tile size in splitting 2D input image, set to 256 as default
    # output: 2D image after passing through tle() and adjust_image()
    tiles = tile(img, size)

    rows = len(tiles)
    cols = len(tiles[0])

    img_fixed = np.zeros((rows * size, cols * size), np.uint8)

    for r in range(rows):
        for c in range(cols):
            img_fixed[r*size:r*size+size, c*size:c*size+size] = adjust_image(tiles[r][c])

    # remove the padding done by the tile function
    return img_fixed[:img.shape[0], :img.shape[1]]


def get_center_of_mask(binary_mask):
    y, x = np.nonzero(binary_mask)
    center_x = int(np.mean(x))
    center_y = int(np.mean(y))
    return center_x, center_y

def get_bounding_box(binary_mask):
    y, x = np.nonzero(binary_mask)
    min_x, max_x = np.min(x), np.max(x)
    min_y, max_y = np.min(y), np.max(y)
    
    # Adjust for 256x256 grid without inverting
    return min_x, 256 - max_y, max_x, 256 - min_y

def detectron_inference():
  # To install:
    # !pip install -q 'git+https://github.com/facebookresearch/detectron2.git'
    # !pip install -q imagecodecs
  # import detectron2
  # from detectron2 import model_zoo
  # from detectron2.engine import DefaultPredictor, DefaultTrainer
  # from detectron2.config import get_cfg
  # from detectron2.utils.visualizer import Visualizer
  # from detectron2.utils.visualizer import ColorMode
  # from detectron2.data import MetadataCatalog, DatasetCatalog
  # from detectron2.utils.events import get_event_storage
  # from detectron2.utils.logger import setup_logger;
  # from detectron2.structures import BoxMode # from pycocotools.mask import encode
  # from detectron2 import model_zoo
  return True