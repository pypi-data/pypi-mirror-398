# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 09:16:30 2024

@author: mfratki
"""

import pandas as pd
from pyhcal import modl_db
from pathlib import Path
import shutil


DEFUALT_REPOSITORY_PATH = Path('X:/Databases2/Water_Quality/Watershed_Modeling/MPCA_HSPF_Model_Repository') #could point to the github website if it becomes public?

class Repository():
    
    HUC_DIRECTORY = pd.read_csv(str(Path(__file__).resolve().parent/'data\\HUC_Names.csv'),dtype = {'USGS HUC-8':'string',
                                                                                                                  'USGS HUC-6':'string',
                                                                                                                  'USGS HUC-4':'string',
                                                                                                                  'USGS HUC-2':'string'})
    
    

    
    

    @classmethod
    def valid_models(self):
        return sorted(list(set(self.HUC_DIRECTORY['Repository_HUC8 Name'].dropna().replace('NO MODEL',pd.NA).dropna().to_list())))
    
    
    def __init__(self,model_name,repository_path = DEFUALT_REPOSITORY_PATH):# = None, huc8_id = None)
        if model_name not in self.valid_models():
            print('Please provide a valid model name (see .valid_models)')
            return
        
        
        self.REPOSITORY_PATH = repository_path
        huc_directory = self.HUC_DIRECTORY.loc[self.HUC_DIRECTORY['Repository_HUC8 Name'] == model_name]
        self.modl_db = modl_db.get_model_db(model_name) #self.MODL_DB.loc[self.MODL_DB['repository_name'] == model_name]
        #self.modl_db  = pd.concat([self.MODL_DB.loc[self.MODL_DB['repository_name'].str.startswith(huc8_id,na=False)] for huc8_id in huc8_ids])        
        self.model_name = model_name
        self.huc8_ids = list(huc_directory['USGS HUC-8'])
        self.huc6_name = huc_directory['Repository_HUC6 Name'].iloc[0]
        self.huc6_id =  huc_directory['USGS HUC-6'].iloc[0]
        self.repo_folder = [item for item in self.REPOSITORY_PATH.joinpath('_'.join([self.huc6_name,self.huc6_id])).iterdir() if item.name.split('_')[0] == self.model_name][0]        
        self.uci_file = self.repo_folder.joinpath('HSPF','.'.join([self.model_name,'uci']))
        self.wdm_files = [item for item in self.repo_folder.joinpath('HSPF').iterdir() if (item.name.endswith('.wdm')) | (item.name.endswith('.WDM'))]
        self.shapefiles = {item.name.split('.')[0].split('_')[-1]:item for item in self.repo_folder.joinpath('GIS').iterdir() if (item.name.endswith('.shp')) | (item.name.endswith('.SHP'))}
        self.wiski_stations = modl_db.wiski_stations(model_name)
        self.equis_stations = modl_db.equis_stations(model_name)


    def copy(self,copy_path):
        copy_path = Path(copy_path)
        build_folders(copy_path)
        shutil.copyfile(self.uci_file, copy_path.joinpath('model','.'.join([self.model_name,'uci'])))
        for wdm_file in self.wdm_files:
            shutil.copyfile(wdm_file,copy_path.joinpath('model',Path(wdm_file).name))
        self.modl_db.to_csv(copy_path.joinpath('_'.join([self.model_name,'MODL_DB.csv'])))
        self.copy_shapefiles(copy_path.joinpath('gis'))

    def copy_wdm(self,copy_path):
        for wdm_file in self.wdm_files:
            shutil.copyfile(wdm_file,Path(copy_path).joinpath(Path(wdm_file).name))

    def copy_uci(self,copy_path):
        shutil.copyfile(self.uci_file, Path(copy_path).joinpath('.'.join([self.model_name,'uci'])))
 
    def copy_modl_db(self,copy_path):
        self.modl_db.to_csv(Path(copy_path).joinpath('_'.join([self.model_name,'MODL_DB.csv'])))

    def copy_shapefiles(self,copy_path):
        for k,shapefile in self.shapefiles.items():
            files = [file for file in shapefile.parent.iterdir() if file.stem == shapefile.stem]
            [shutil.copyfile(file,Path(copy_path).joinpath(Path(file).name)) for file in files]
            
    
    
def build_folders(trg_path):
    
    sub_folders = ['model',
                   'output',
                   'inputs',
                   'figures',
                   'gis',
                   'data']
    
    
    trg_path = Path(trg_path)
    #p = Path(build_path) 
    #trg_path = p.joinpath(project_name)
    if not trg_path.is_dir():
        trg_path.mkdir(parents=True)
    
    for path in sub_folders:
        if not trg_path.joinpath(path).is_dir():
            trg_path.joinpath(path).mkdir()

      
