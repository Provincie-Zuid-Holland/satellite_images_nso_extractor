import rasterio
import tqdm
import numpy as np
import pandas as pd
import glob

def generate_ndvi_channel(tile):
        """
        Generate ndvi channel from 2 bands.
        
        @param tile: rgbi tile to calculate to the NDVI from.
        @return a NDVI channel.
        """
        print("Generating NDVI channel...")
        red = tile[0]
        nir = tile[3]
        ndvi = []

        # None numpy way.
        for i in tqdm.tqdm(range(len(red))):
            ndvi_x = []
            for x in range(len(red[i])):
                upper_ndvi = (int(nir[i][x]-int(red[i][x])))
                lower_ndvi = (int(nir[i][x])+int(red[i][x]))

                if lower_ndvi == 0:
                    ndvi_x.append(0)
                else:
                    ndvi_cur = upper_ndvi/lower_ndvi
                    ndvi_cur = (ndvi_cur*100)+100
                    ndvi_x.append(int(ndvi_cur))
            ndvi.append(ndvi_x)

        #for i in tqdm.tqdm(range(len(red))):
        #        ndvi.append(np.nan_to_num(np.divide(np.subtract(nir[i],red[i]), np.add(nir[i],red[i]))))  

        return ndvi


for file in glob.glob("E:/data/coepelduynen/*ndvi_height.tif"):
    file.replace("\\","/")
    print(file)
    inds = rasterio.open(file, 'r') 
    tile = inds.read()

    ndvi = generate_ndvi_channel(tile)

    inds.close()


 
    with rasterio.open(file 'w', **meta) as outds:        
                outds.write_band(1,tile[0])
                outds.write_band(2,tile[1])
                outds.write_band(3,tile[2])
                outds.write_band(4,tile[3])
                outds.write_band(5,np.array(ndvi))
                outds.write_band(6,tile[5])
                outds.close()
  
    inds.close() 