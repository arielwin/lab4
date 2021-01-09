import numpy as np
import rasterio
from rasterio.plot import show, show_hist
import glob
from scipy.spatial import cKDTree
import pandas as pd
from shapely.geometry import Point, LineString, Polygon
from rasterio.enums import Resampling
import random
from scipy.spatial import distance

#Get tifs from data folder
rasters = glob.glob(r'data/*.tif')

#remove two tifs not needed in analysis
rasters.pop(1)
rasters.pop(2)

#creat an empty array for assignment of averaged arrays
arrays = []

def meanWindow(rasters):
    '''
    Function that accepts list of arrays. Moves a window of size 11X9 across the array and gets the average in that window
    Addigns output arrays to empty list called 'arrays'
    '''
    
    #for each raster in list of rasters
    for raster in rasters:

        with rasterio.open(raster) as data:                       #open each raster.tif
            array = data.read(1)                                  #open each tif as array
            array = np.where(array < 0 , 0, array)                #if any values are less than 0, remove them
            meanArray = np.zeros_like(array)#, dtype = np.float64)   #create an array of zeros, the same shape as the input array

            for row in range(5, array.shape[0] - 5):             #nested
                for col in range(4, array.shape[1] - 4):          #for loops
                    win = array[row-5:row + 10, col -4 : col + 8]#create a window of zie 11rowx9col populated with data from input array
                    meanArray[row,col] = win.mean()              #average the data in that window and assign it to array populated with zeros
            arrays.append(meanArray)                             #append that array data to the list of arrays
            
meanWindow(rasters)

arrays[0] = np.where(arrays[0] < 0.05, 1 , 0)                #if less than 5%, 1, else 0

arrays[1] = np.where(arrays[1] < 15, 1 , 0)                  #if less than 15%, 1, else 0

arrays[2] = np.where(arrays[2] != 0, 0 , 1)                  #if 0, 1, else 0

arrays[3] = np.where(arrays[3] < 0.02, 1 , 0)                #if less than 2%, 1, else 0

arrays[4] = np.where(arrays[4] < 8.5, 0 ,1)                  #if less than 8.5, 0, else 1

aris = arrays[0] +arrays[1] +arrays[2] +arrays[3] +arrays[4] #add all 5 arrays, places where 1s overlap, we get 5s and have suitable areas

suitable_areas = np.where(aris == 5, 1, 0)                              #if 5, set as 1, else set as 0

print('The total number of suitable sites is' , suitable_areas.sum())   #sum all 1s to see total number of suitable sites


#converts suitable_areas array into a tif called suitable_area
with rasterio.open(r'data/slope.tif') as dataset:

    with rasterio.open(f'suitable_area.tif' , 'w', 
                       driver='GTiff',
                       height=suitable_areas.shape[0],
                       width=suitable_areas.shape[1],
                       count=1,
                       dtype=suitable_areas.dtype,
                       crs=dataset.crs,
                       transform=dataset.transform,
                       nodta=dataset.nodata
                      ) as out_dataset:
        out_dataset.write(suitable_areas,1)

xs = []
ys = []
#extract x,y values from .txt file and assign them to list called stations
with open(r'data/transmission_stations.txt') as coords:
    lines = coords.readlines()[1:]
    for l in lines:
        x,y = l.split(',')
        xs.append(float(x))
        ys.append(float(y))
    stations = np.vstack([xs, ys])
    stations = stations.T
    
with rasterio.open(r'suitable_area.tif') as file:
    
    bounds = file.bounds              #get bounds of suitable areas file
    topLeft = (bounds[0], bounds[3])  #top left bound
    lowRight = (bounds[2], bounds[1]) #bottom right bound
    cellSize = 1000                   #cell size

    x_coords = np.arange(topLeft[0] + cellSize/2, lowRight[0], cellSize)
    y_coords = np.arange(lowRight[1] + cellSize/2, topLeft[1], cellSize)
    
    xx, yy = np.meshgrid(x_coords, y_coords) #create coordinate pairs
    coords = np.c_[xx.ravel(), yy.ravel()]   #array like a list of coord pairs
    ravel_coords = xx.ravel()

    ones = suitable_areas.reshape(ravel_coords.shape) #reshape suitable areas array to shape of coords

    new_coords = []                  #empty list for coords of suitable sites
    for i, e in zip(coords, ones):   #run through all the entries
        x = np.multiply(i[0], e)     #get x coord and multiply it by cell in suitable sites array
        y = np.multiply(i[1], e)     #get y coord and multiply it by cell in suitable sites array
        if x != 0 and y != 0:        #if the cell in suitbale sites is 0, x, y will equal zero
            new_coords.append([x, y])#append coord pairs that match suitable sites

    dist, indices = cKDTree(stations).query(new_coords) #run the euclidean distance
    
    print('The maximum distance is: ' + str(dist.max()/1000)) #print max distance from list
    print('The minimum distance is: ' + str(dist.min()/1000)) #print min distance from list
