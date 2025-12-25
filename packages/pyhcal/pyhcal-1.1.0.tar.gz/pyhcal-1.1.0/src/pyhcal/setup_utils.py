# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 15:21:35 2022

@author: mfratki
"""
from mpcaHydro.data_manager import dataManager
from hspf.wdmReader import readWDM
from hspf.uci import UCI
from pyhcal.repository import Repository
from pyhcal import modl_db

import numpy as np
import pandas as pd
from pathlib import Path
import subprocess


def create_calibration_project(model_name,project_location,download_station_data = True,run_model = True,convert_wdms = True):
    project = Builder(model_name)
    project.copy(project_location,model_name)
    project.load_uci()
    project.format_uci()
    project.uci.build_targets().to_csv(project.project_path.joinpath('targets.csv'))
    if convert_wdms: project.convert_wdms()
    if download_station_data: project.download_station_data()
    if run_model: project.run_model()
   
    
    
    

class Builder():
    
    def __init__(self,model_name):
        self.repository = Repository(model_name)
        self.project_path = None
        self.project_name = None
        self.new_uci = None
        self.uci = None
        self.dm = None
        self.calibration_reaches = modl_db.wplmn_station_opnids(model_name)

    
    def valid_models():
        return Repository.valid_models()
    
    def set_project_path(self,project_path):
        self.project_path = Path(project_path)
        self.project_name = Path(project_path).name
        #self.new_uci = self.project_path.joinpath('model','_'.join([self.project_name,'0.uci']))
        #self.uci = UCI(self.project_path.joinpath('model','.'.join([self.project_name,'uci'])))
        
    def copy(self,project_location,project_name):
        self.project_path = Path(project_location).joinpath(project_name)
        self.project_name = project_name
        self.repository.copy(self.project_path)
        self.dm = dataManager(self.project_path.joinpath('data'))

    
    def load_uci(self):
        self.new_uci = self.project_path.joinpath('model','_'.join([self.project_name,'0.uci']))
        self.uci = UCI(self.project_path.joinpath('model','.'.join([self.project_name,'uci'])))

    def process(self):
        self.load_uci()
        self.format_uci()
        self.download_station_data()
        self.uci.build_targets().to_csv(self.project_path.joinpath('targets.csv'))

    
    def format_uci(self,calibration_reaches = None):
        if calibration_reaches is None:
            calibration_reaches = self.calibration_reaches

        setup_files(self.uci,self.project_name,run = 0)
        setup_geninfo(self.uci)
        self.uci.initialize(name = self.project_name + '_0')  
        setup_binaryinfo(self.uci,reach_ids = calibration_reaches)
        setup_qualid(self.uci)
        self.uci.write(self.new_uci)
        
    
    def download_station_data(self,start_year,end_year):#:,station_id,source_id):
        #%% Old approach. Store as indvidual processed station files then load to warehouse
        if len(equis_stations) > 0:
            if self.dm.credentials_exist():
                station_origin = 'equis'
            else: station_origin = 'swd'
        
            for station_id in equis_stations:
                self.dm.download_station_data(station_id,station_origin, True)
        
        if len(wiski_stations) > 0:
            for station_id in wiski_stations:
                self.dm.download_station_data(station_id,'wiski', True)
                 
    
    def convert_wdms(self):
        copy_path = Path(self.project_path.joinpath('model'))
        wdm_files = [copy_path.joinpath(wdm_file.name) for wdm_file in self.repository.wdm_files]
        for wdm_file in wdm_files:
            readWDM(wdm_file,
                    copy_path.joinpath(wdm_file.name.replace('.wdm','.hdf5').replace('.WDM','hdf5')))
        
    def run_model(self, wait_for_completion=True):
        #run_model(self.new_uci, wait_for_completion)
        # Run the uci file
        winHSPF = str(Path(__file__).resolve().parent.parent) + '\\bin\\WinHSPFLt\\WinHspfLt.exe'     
        subprocess.run([winHSPF,self.new_uci]) #, stdout=subprocess.PIPE, creationflags=0x08000000)    
        
def run_model(uci_file, wait_for_completion=True):
    winHSPF = str(Path(__file__).resolve().parent.parent) + '\\bin\\WinHSPFlt\\WinHspfLt.exe'
    
    # Arguments for the subprocess
    args = [winHSPF, uci_file.as_posix()]

    if wait_for_completion:
        # Use subprocess.run to wait for the process to complete (original behavior)
        subprocess.run(args)
    else:
        # Use subprocess.Popen to run the process in the background without waiting
        # On Windows, you can use creationflags to prevent a console window from appearing
        if sys.platform.startswith('win'):
            # Use a variable for the flag to ensure it's only used on Windows
            creationflags = subprocess.CREATE_NO_WINDOW
            subprocess.Popen(args, creationflags=creationflags)
        else:
            # For other platforms (like Linux/macOS), Popen without special flags works fine
            subprocess.Popen(args)



### functions for setting up the UCI file properly 
def setup(uci,name,run = 0,reach_ids = None,n = 1,time_step = 3):
    uci = setup_files(uci,name,run,n)
    uci = setup_geninfo(uci)
    uci = setup_binaryinfo(uci,reach_ids = reach_ids)
    uci = setup_qualid(uci)


#def setup_files(uci,name,run = 0,n=5): # Add as method to a Files class?
#    # Update paths in Files block
    
def setup_files(uci,name,run,n = 5):
    table = uci.table('FILES',drop_comments = False)
    for index, row in table.iterrows():
        filename = Path(row['FILENAME'])
        if filename.suffix in ['.wdm','.ech','.out','.mut']:
            table.loc[index,'FILENAME'] = filename.name
        elif filename.suffix in ['.hbn']:
            table.loc[index,'FILENAME'] = filename.name
        #if filename.suffix in ['.plt']:
        else:
            table.drop(index,inplace = True)
            
    # Get new binary number and create new BINO rows
    bino_nums = []
    invalid = table['UNIT'].values
    for num in range(15,100):
        if num not in invalid:
            bino_nums.append(num)
        if len(bino_nums) == n:
            break
    binary_names = ['_'.join([name,str(run)])+ '-' + str(num) + '.hbn' for num in range(len( bino_nums))]
    rows = [['BINO',bino_num,binary_name,''] for bino_num,binary_name in zip(bino_nums,binary_names)]
    rows = pd.DataFrame(rows, columns = table.columns).astype({'FTYPE':'string','UNIT':'Int64','FILENAME':'string','comments':'string'} )
    # Drop old BINO rows and insert new BINO rows
    table = table.loc[table['FTYPE'] != 'BINO'].reset_index(drop=True)
    rows = pd.DataFrame(rows, columns = table.columns).astype(table.dtypes) #{'FTYPE':'string','UNIT':'Int64','FILENAME':'string','comments':'string'} )
    table = pd.concat([table,rows])
    table.reset_index(drop=True,inplace=True)
    
    # Update table in the uci
    uci.replace_table(table,'FILES')
    
    return uci

def setup_geninfo(uci):
    # Initialize Gen-Info
    bino_nums = uci.table('FILES').set_index('FTYPE').loc['BINO','UNIT'].tolist()
    if isinstance(bino_nums,int): #Pands is poorly designed. Why would tolist not return a goddamn list...?
        bino_nums = [bino_nums]
  
    #opnids = uci.table(operation,'GEN-INFO').index
    for operation in ['RCHRES','PERLND','IMPLND']:
        opnids = np.array_split(uci.table(operation,'GEN-INFO').index.to_list(),len(bino_nums))
        
        for opnid,bino_num in zip(opnids,bino_nums):
            if operation == 'RCHRES': #TODO convert BUNITE to BUNIT1 to get rid of this if statement
                uci.update_table(bino_num,'RCHRES','GEN-INFO',0,opnids = opnid,columns = 'BUNITE',operator = 'set')
            else:
                uci.update_table(bino_num,operation,'GEN-INFO',0,opnids = opnid,columns = 'BUNIT1',operator = 'set')
    return uci     

def setup_binaryinfo(uci,default_output = 4,reach_ids = None):
    # Initialize Binary-Info
    uci.update_table(default_output,'PERLND','BINARY-INFO',0,
                     columns = ['AIRTPR', 'SNOWPR', 'PWATPR', 'SEDPR', 'PSTPR', 'PWGPR', 'PQALPR','MSTLPR', 'PESTPR', 'NITRPR', 'PHOSPR', 'TRACPR'],
                     operator = 'set')
    uci.update_table(default_output,'IMPLND','BINARY-INFO',0,
                     columns = ['ATMPPR', 'SNOWPR', 'IWATPR', 'SLDPR', 'IWGPR', 'IQALPR'],
                     operator = 'set')
    uci.update_table(default_output,'RCHRES','BINARY-INFO',0, 
                     columns = ['HYDRPR', 'ADCAPR', 'CONSPR', 'HEATPR', 'SEDPR', 'GQLPR', 'OXRXPR', 'NUTRPR', 'PLNKPR', 'PHCBPR'],
                     operator = 'set')
        
    uci.update_table(default_output,'PERLND','BINARY-INFO',0,columns = ['SNOWPR','SEDPR','PWATPR','PQALPR'],operator = 'set')
    uci.update_table(default_output,'IMPLND','BINARY-INFO',0,columns = ['SNOWPR','IWATPR','SLDPR','IQALPR'],operator = 'set')
    uci.update_table(default_output,'RCHRES','BINARY-INFO',0,columns = ['HYDRPR','SEDPR','HEATPR','OXRXPR','NUTRPR','PLNKPR'],operator = 'set')
    if reach_ids is not None:
        uci.update_table(3,'RCHRES','BINARY-INFO',0,columns = ['SEDPR','OXRXPR','NUTRPR','PLNKPR'],opnids = reach_ids,operator = 'set')
        uci.update_table(2,'RCHRES','BINARY-INFO',0,columns = ['HEATPR','HYDRPR'],opnids = reach_ids,operator = 'set')
    return uci     


def setup_qualid(uci):
    #### Standardize QUAL-ID Names
    # Perlands
    uci.update_table('NH3+NH4','PERLND','QUAL-PROPS',0,columns = 'QUALID',operator = 'set')
    uci.update_table('NO3','PERLND','QUAL-PROPS',1,columns = 'QUALID',operator = 'set')
    uci.update_table('ORTHO P','PERLND','QUAL-PROPS',2,columns = 'QUALID',operator = 'set')
    uci.update_table('BOD','PERLND','QUAL-PROPS',3,columns = 'QUALID',operator = 'set')
    
    # Implands
    uci.update_table('NH3+NH4','IMPLND','QUAL-PROPS',0,columns = 'QUALID',operator = 'set')
    uci.update_table('NO3','IMPLND','QUAL-PROPS',1,columns = 'QUALID',operator = 'set')
    uci.update_table('ORTHO P','IMPLND','QUAL-PROPS',2,columns = 'QUALID',operator = 'set')
    uci.update_table('BOD','IMPLND','QUAL-PROPS',3,columns = 'QUALID',operator = 'set')
    return uci     



# def build_targets(uci,reach_ids,wplmn_map,wplmn_path,wplmn = None):
#     targets = uci.lc_info()
#     uci_names = targets['uci_name'].values
#     if wplmn is None:
#         wplmn = get_yields(reach_ids,uci,wplmn_path)
   
#     npsl_names = [wplmn_map[name] for name in targets['uci_name']]
#     targets['npsl_name'] = npsl_names #targets['npsl_name'] = npsl_names
    
    
    
#     npsl_rates = pd.concat([uci.npsl_targets.loc[name].mean() for name in npsl_names],axis = 1).transpose()
#     npsl_rates['uci_name'] = uci_names
#     npsl_rates = npsl_rates.melt(id_vars = 'uci_name',var_name = 'parameter', value_name = 'npsl_yield')
    
#     targets = npsl_rates.merge(targets,on = 'uci_name')
#     targets = targets.set_index(['uci_name','parameter'])
    
#     # normalize by dominant landcover of the model
#     dom_lc_name =  targets.index.get_level_values(0)[np.argmax(targets['area'])]
#     targets['npsl_yield_ratio'] = np.nan
#     for parameter in ['TSS','TKN','N','OP','BOD']:
#         values = targets.loc[:,parameter,:]['npsl_yield']/targets.loc[dom_lc_name,parameter]['npsl_yield']
#         targets.loc[values.index,'npsl_yield_ratio'] = values
    
#     # landcover area ratio compared to total area of watershed
#     targets['lc_area_ratio']= targets['area']/np.sum(targets.loc[:,'TSS',:]['area'])    
    
    
#     targets['wplmn_yield'] = np.nan
#     for parameter in ['TSS','TKN','N','OP','BOD']:
#         targets.loc[targets.loc[:,parameter,:].index,'wplmn_yield'] = wplmn[parameter]
      
#     # interative solution to determine target landcover loading rates
#     targets['lc_yield'] = np.nan
#     threshold = .05
#     for parameter in ['TSS','TKN','N','OP','BOD']:
#         print(parameter)
#         diff = 1
#         scaling_factor = 1
#         new_factor = 1
#         while diff > threshold:
#             scaling_factor = new_factor
#             lc_yield =  (targets['lc_area_ratio']*targets['npsl_yield_ratio']*scaling_factor).loc[:,parameter,:]
#             new_factor = wplmn[parameter]/np.sum(lc_yield)*scaling_factor
#             diff = np.abs((np.nansum(lc_yield)-wplmn[parameter])/wplmn[parameter])
#         print(scaling_factor)
#         values = targets.loc[targets.loc[:,parameter,:].index,'npsl_yield_ratio']*scaling_factor
#         targets.loc[values.index,'lc_yield'] = values.values
    

#     targets = uci.lc_info().set_index('uci_name').join(targets.unstack()['lc_yield'])
#     targets['dom_lc'] = np.nan
#     targets.loc[targets.index[np.argmax(targets['area'])],'dom_lc'] = 1
#     return targets

# def get_yields(reach_ids,uci,wplmn_path):
#     loadNetwork = dm.loadNetwork(wplmn_path,reach_ids)
    
#     schematic = uci.table('SCHEMATIC')
#     schematic = schematic.astype({'TVOLNO': int, "SVOLNO": int, 'AFACTR':float})
#     schematic = schematic[(schematic['SVOL'] == 'PERLND')| (schematic['SVOL'] == 'IMPLND')]
#     schematic = schematic[schematic['TVOL'] == 'RCHRES']
#     reaches = np.concatenate([nu.get_opnids(uci,reach_id)[0] for reach_id in reach_ids])
#     area = np.sum([schematic['AFACTR'][schematic['TVOLNO'] == reach].sum() for reach in reaches])
    
    
#     # wplmn2 = {'TSS': 18.01,
#     #           'TP': 0.23,
#     #           'OP':0.082,
#     #           'TKN':1.921,
#     #           'N':2.304}
#     # wplmn2['BOD'] = 50*(wplmn['TP'] - wplmn['OP'])
#     # wplmn2['TKN'] = wplmn['TKN'] - wplmn['BOD']*.144

#     wplmn = {'TSS': 0,
#               'TP': 0,
#               'OP':0,
#               'TKN':0,
#               'N':0}
    
#     for key in wplmn.keys():
#         if key == 'TSS':
#             wplmn[key] = np.mean(loadNetwork.get_timeseries(key,'Load').groupby('year').sum()['Ts Value']/area*2000)
#         else:
#             wplmn[key] = np.mean(loadNetwork.get_timeseries(key,'Load').groupby('year').sum()['Ts Value']/area)

        
#     wplmn['BOD'] = 50*(wplmn['TP'] - wplmn['OP'])
#     wplmn['TKN'] = wplmn['TKN'] - wplmn['BOD']*.144
#     return wplmn

# def lc_info(uci):
#     uci.get_metzones2()
#     geninfo = uci.table('PERLND','GEN-INFO')  
#     targets = uci.opnid_dict['PERLND'].loc[:,['LSID','landcover']] #.drop_duplicates(subset = 'landcover').loc[:,['LSID','landcover']].reset_index(drop = True)
#     targets.columns = ['LSID','lc_number']
#     schematic = uci.table('SCHEMATIC')
#     schematic = schematic.astype({'TVOLNO': int, "SVOLNO": int, 'AFACTR':float})
#     schematic = schematic[(schematic['SVOL'] == 'PERLND')]
#     schematic = schematic[(schematic['TVOL'] == 'PERLND') | (schematic['TVOL'] == 'IMPLND') | (schematic['TVOL'] == 'RCHRES')]
#     areas = []
#     for lc_number in targets['lc_number'].unique():
#         areas.append(np.sum([schematic['AFACTR'][schematic['SVOLNO'] == perland].sum() for perland in targets.index[targets['lc_number'] == lc_number]]))
#     areas = np.array(areas)
    
    
#     lc_number = targets['lc_number'].drop_duplicates()
#     uci_names = geninfo.loc[targets['lc_number'].drop_duplicates().index]['LSID']
#     targets = pd.DataFrame([uci_names.values,lc_number.values,areas]).transpose()
#     targets.columns = ['uci_name','lc_number','area']
#     targets['npsl_name'] = ''
    
#     targets[['TSS','N','TKN','OP','BOD']] = ''
    
#     targets['dom_lc'] = ''
#     targets.loc[targets['area'].astype('float').argmax(),'dom_lc'] = 1
#     return targets





#WPLMN = pd.read_csv()
# HUC_DIRECTORY = pd.read_csv('C:/Users/mfratki/Documents/Github/hspf_tools/calibrator/HUC_Names.csv',dtype = {'USGS HUC-8':'string',
#                                                                                                              'USGS HUC-6':'string',
#                                                                                                              'USGS HUC-4':'string',
#                                                                                                              'USGS HUC-2':'string'})
#MODL_DB = pd.read_csv('C:/Users/mfratki/Documents/Github/hspf_tools/calibrator/WPLMN.csv',dtype = {'stn_HUC12':'string'})


# REPO = Path('X:\Databases2\Water_Quality\Watershed_Modeling\MPCA_HSPF_Model_Repository') #could point to the github website if it becomes public
# huc8_id = '10170204'
# huc6_name = HUC_DIRECTORY.loc[HUC_DIRECTORY['USGS HUC-6'] == huc8_id[:6],'Repository_HUC6 Name'].iloc[0]
# model_name = HUC_DIRECTORY.loc[HUC_DIRECTORY['USGS HUC-8'] == huc8_id[:8],'Repository_HUC8 Name'].iloc[0]
# repo_folder = [item for item in REPO.joinpath('_'.join([huc6_name,huc8_id[:6]])).iterdir() if item.name.startswith(model_name)]
# repo_folder = repo_folder[0]    

# stations = gpd.read_file('C:/Users/mfratki/Documents/Projects/MODL Database/stations_WISKI2.gpkg')
# stations.dropna(subset='stn_HUC12',inplace=True)
# stations['opnids'] = stations['opnids'].str.replace('-','+')
# HUC_DIRECTORY = pd.read_csv('C:/Users/mfratki/Documents/Github/hspf_tools/calibrator/HUC_Names.csv',dtype = {'USGS HUC-8':'string',
#                                                                                                               'USGS HUC-6':'string',
#                                                                                                               'USGS HUC-4':'string',
#                                                                                                               'USGS HUC-2':'string'})
# test = pd.merge(wiski, HUC_DIRECTORY, left_on=  'HUC8',
#                     right_on= 'USGS HUC-8', 
#                     how = 'left')
# class Builder():
#     # HUC_DIRECTORY = pd.read_csv('C:/Users/mfratki/Documents/Github/hspf_tools/calibrator/HUC_Names.csv',dtype = {'USGS HUC-8':'string',
#     #                                                                                                               'USGS HUC-6':'string',
#     #                                                                                                               'USGS HUC-4':'string',
#     #                                                                                                               'USGS HUC-2':'string'})
#     # MODL_DB = pd.read_csv('C:/Users/mfratki/Documents/Github/hspf_tools/calibrator/WPLMN.csv',dtype = {'stn_HUC12':'string',
#     #                                                                                                    'USGS HUC-8':'string',
#     #                                                                                                    'USGS HUC-6':'string',
#     #                                                                                                    'USGS HUC-4':'string',
#     #                                                                                                    'USGS HUC-2':'string'}

#     # MODL_DB = pd.read_csv(Path(__file__).parent/'stations_WISKI.csv',dtype = {'stn_HUC12':'string',              
#     #                                                                           'USGS HUC-8':'string',
#     #                                                                           'USGS HUC-6':'string',
#     #                                                                           'USGS HUC-2':'string',
#     #                                                                           'USGS HUC-4':'string'})
#     # MODL_DB = pd.read_csv('C:/Users/mfratki/Documents/Projects/MODL Database/stations_WISKI.csv', dtype = {'stn_HUC12':'string',              
#     #                                                                                                        'USGS HUC-8':'string',
#     #                                                                                                        'USGS HUC-6':'string',
#     #                                                                                                        'USGS HUC-4':'string',
#     #                                                                                                        'USGS HUC-2':'string'})                                                                                                       

#     MODL_DB = gpd.read_file('C:/Users/mfratki/Documents/Projects/MODL Database/gis/stations_csg.gpkg').dropna(subset='opnids')
#     #MODL_DB = gpd.read_file('C:/Users/mfratki/Documents/Projects/MODL Database/stations_WISKI2.gpkg')  #.dropna(subset='opnids')
#     #MODL_DB['opnids'] = MODL_DB['opnids'].str.replace('-','+')    
#     MODL_DB = MODL_DB.dropna(subset='opnids')
#     MODL_DB = MODL_DB.loc[~(MODL_DB['opnids'] == -1)]
#     REPO = Path('X:\Databases2\Water_Quality\Watershed_Modeling\MPCA_HSPF_Model_Repository') #could point to the github website if it becomes public
    
#     @classmethod
#     def valid_models(self):
#         return list(self.MODL_DB['Repository_HUC8 Name'].dropna()) #replace('NO MODEL',pd.NA).dropna())

                
#     def __init__(self,model_name):# = None, huc8_id = None)
#         if model_name not in self.valid_models():
#             print('Please provide a valid model name (see .valid_models)')
#             return
            
#         self.model_name = model_name
#         #self._HUC_DIRECTORY = self.HUC_DIRECTORY.loc[self.HUC_DIRECTORY['Repository_HUC8 Name'] == self.model_name]
#         #self.huc6_name = self._HUC_DIRECTORY['Repository_HUC6 Name'].iloc[0]
#         #self.huc8_id = self._HUC_DIRECTORY['USGS HUC-8'].iloc[0] #HUC_DIRECTORY.loc[HUC_DIRECTORY['USGS HUC-6'] == huc8_id[:6],'Repository_HUC6 Name'].iloc[0]
        
#         self._MODL_DB = self.MODL_DB.loc[self.MODL_DB['Repository_HUC8 Name'] == self.model_name]
#         self.huc6_name = self._MODL_DB['Repository_HUC6 Name'].iloc[0]
#         self.huc6_id = self._MODL_DB['USGS HUC-6'].iloc[0]
#         self.huc8_ids = self._MODL_DB['USGS HUC-8'].unique()
#         self.repo_folder = [item for item in self.REPO.joinpath('_'.join([self.huc6_name,self.huc6_id])).iterdir() if item.name.startswith(self.model_name)][0]        
#         self.uci_file = self.repo_folder.joinpath('HSPF','.'.join([self.model_name,'uci']))
#         self.wdm_files = [item for item in self.repo_folder.joinpath('HSPF').iterdir() if item.name.endswith('.wdm')]
    
#     def copy(self,project_location):


#         build_folders(self.model_name,project_location)
#         self.project_path = Path(project_location).joinpath(self.model_name)
#         self.new_uci = self.project_path.joinpath('model','_'.join([self.model_name,'0.uci']))
#         shutil.copyfile(self.uci_file, self.project_path.joinpath('model','.'.join([self.model_name,'uci'])))
#         self.uci = UCI(self.project_path.joinpath('model','.'.join([self.model_name,'uci'])))
#         for wdm_file in self.wdm_files:
#             shutil.copyfile(wdm_file,self.project_path.joinpath('model',Path(wdm_file).name))
    
        
#         self.format_uci()
#         self.download_wplmn()
#         self.download_csg()
#         self.build_lc_targets()
#         if not self.project_path.joinpath('model',self.model_name + '_0-0.hbn').exists():
#             self.run_model()
#         self._MODL_DB.to_csv(self.project_path.joinpath('_'.join([self.model_name,'MODL_DB.csv'])))
        
#     def format_uci(self):
        
#         setup_files(self.uci,self.model_name,run = 0)
#         setup_geninfo(self.uci)
        
#         calibration_reaches = self._MODL_DB['opnids'].astype('int').to_list()
#         # for reaches in self._MODL_DB['opnids'].str.split('+').to_list():
#         #     [calibration_reaches.append(int(reach)) for reach in reaches if ~pd.isna(reach)]
            
#         setup_binaryinfo(self.uci,reach_ids = calibration_reaches)
#         setup_qualid(self.uci)
#         self.uci.write(self.new_uci)
        
#         # Download observation data
#         # Sources/Databases WISKI and EQUIS (DELTA databases?)
#     #TODO: use a single WISKI etl script for csg and wplmn data
#     def download_csg(self):
#         if self.project_path.joinpath('csg.csv').exists():
#             print('CSG data already downloaded')
#         station_nos = (self._MODL_DB.loc[self._MODL_DB['WPLMN'] == 0,'station_no'].unique())
#         if len(station_nos) == 0:
#             print('No CSG stations linked to Watershed yet')
#             return
#         data = pd.concat([etlCSG.download(station_no).pipe(etlCSG.transform) for station_no in station_nos])
#         #reach_map = dict(self._MODL_DB.loc[self._MODL_DB['station_no'].isin(station_nos),['station_no','opnids']].values)
#         #data['reach_id'] = data['station_no'].map(reach_map)
#         etlCSG.load(data,self.project_path.joinpath('csg.csv'))
             
#     def download_wplmn(self):
#         if self.project_path.joinpath('wplmn.csv').exists():
#             print('WPLMN data already downloaded')
#         station_nos = list(self._MODL_DB.loc[self._MODL_DB['WPLMN'] == 1,'station_no'].unique())
#         data = pd.concat([etlWPLMN.download(station_no).pipe(etlWPLMN.transform) for station_no in station_nos])
#         #reach_map = dict(self._MODL_DB.loc[self._MODL_DB['station_no'].isin(station_nos),['station_no','opnids']].values)
#         #data['reach_id'] = data['Station number'].map(reach_map)
#         etlCSG.load(data,self.project_path.joinpath('wplmn.csv'))
    
#     def download_swd(self):
#         if self.project_path.joinpath('swd.csv').exists():
#             print('SWD data already downloaded')
#         station_nos = list(self._MODL_DB.loc[self._MODL_DB['source'] == 'swd','station_no'].unique())
#         data = pd.concat([etlSWD.download(station_no).pipe(etlSWD.transform) for station_no in station_nos])
#         etlSWD.load(data,self.project_path.joinpath('swd.csv'))

#         # Create landcover targets spreadsheet
#     def build_lc_targets(self):
#         lc_info(self.uci).to_csv(self.project_path.joinpath('targets.csv'))
        
#     def run_model(self):
#         # Run the uci file
#         winHSPF = str(Path(__file__).resolve().parent.parent) + '\\bin\\WinHSPFLt\\WinHspfLt.exe'     
#         subprocess.run([winHSPF,self.new_uci]) #, stdout=subprocess.PIPE, creationflags=0x08000000)    
        

#         # if (model_name is None) & (huc8_id is None):
#         #     print('Please provide Either a HUC8 ID or a valid model name. To see valid model names see .valid_models')
#         #     return
#         #if model_name is None:
#         # else:
#         #     self._HUC_DIRECTORY = self.HUC_DIRECTORY.loc[self.HUC_DIRECTORY['Repository_HUC8 Name',:]
#         #     self.huc6_name = self._HUC_DIRECTORY.loc[0,'Repository_HUC6 Name']
#         #     self.model_name = self._HUC_DIRECTORY.loc[0,'Repository_HUC8 Name']
#         #     self.repo_folder = 





# load original uci

# def setup_files(uci,project_name): # Add as method to a Files class?
#     # Update paths in Files block
#     table = uci.table('FILES',drop_comments = False)
#     for index, row in table.iterrows():
#         name = Path(row['FILENAME'])
#         if name.suffix in ['ech','out','wdm']:
#             table.loc[index,'FILENAME'] = name
#         if name.suffix in ['hbn']:
#             table.loc[index,'FILENAME'] = name
#         if name.suffix in ['plt']:
#             table.drop(index)
    
#     table = table.set_index(table.columns[0])


#     # Rename hbn in Files block
#     #TODO: dynamic size management of hbn files
#     new_bino = table.loc['BINO'][~table.loc['BINO'].index.duplicated()]
#     table = table.drop('BINO',axis=0)
#     table = table.append(new_bino)
#     table.loc['BINO','FILENAME'] = project_name + '_0.hbn'
#     table = table.reset_index()
#     uci.replace_table(table,'FILES')        
#     return uci     


# def setup_geninfo(uci):
#     # Initialize Gen-Info
#     bino_num = uci.table('FILES').set_index('FTYPE').loc['BINO','UNIT']
#     uci.update_table(bino_num,'PERLND','GEN-INFO',0,columns = 'BUNIT1',operator = 'set')
#     uci.update_table(bino_num,'RCHRES','GEN-INFO',0,columns = 'BUNITE',operator = 'set')
#     uci.update_table(bino_num,'IMPLND','GEN-INFO',0,columns = 'BUNIT1',operator = 'set')
#     return uci     

# def setup_binaryinfo(uci,reach_ids = None):
#     # Initialize Binary-Info
#     uci.update_table(4,'PERLND','BINARY-INFO',0,columns = ['SNOWPR','SEDPR','PWATPR','PQALPR'],operator = 'set')
#     uci.update_table(4,'IMPLND','BINARY-INFO',0,columns = ['SNOWPR','IWATPR','SLDPR','IQALPR'],operator = 'set')
#     uci.update_table(4,'RCHRES','BINARY-INFO',0,columns = ['HYDRPR','SEDPR','HEATPR','OXRXPR','NUTRPR','PLNKPR'],operator = 'set')
#     if reach_ids is not None:
#         uci.update_table(3,'RCHRES','BINARY-INFO',0,columns = ['HYDRPR','SEDPR','HEATPR','OXRXPR','NUTRPR','PLNKPR'],opnids = reach_ids,operator = 'set')
#     return uci     

# def setup_qualid(uci):
#     #### Standardize QUAL-ID Names
#     # Perlands
#     uci.update_table('NH3+NH4','PERLND','QUAL-PROPS',0,columns = 'QUALID',operator = 'set')
#     uci.update_table('NO3','PERLND','QUAL-PROPS',1,columns = 'QUALID',operator = 'set')
#     uci.update_table('ORTHO P','PERLND','QUAL-PROPS',2,columns = 'QUALID',operator = 'set')
#     uci.update_table('BOD','PERLND','QUAL-PROPS',3,columns = 'QUALID',operator = 'set')
    
#     # Implands
#     uci.update_table('NH3+NH4','IMPLND','QUAL-PROPS',0,columns = 'QUALID',operator = 'set')
#     uci.update_table('NO3','IMPLND','QUAL-PROPS',1,columns = 'QUALID',operator = 'set')
#     uci.update_table('ORTHO P','IMPLND','QUAL-PROPS',2,columns = 'QUALID',operator = 'set')
#     uci.update_table('BOD','IMPLND','QUAL-PROPS',3,columns = 'QUALID',operator = 'set')
#     return uci     






