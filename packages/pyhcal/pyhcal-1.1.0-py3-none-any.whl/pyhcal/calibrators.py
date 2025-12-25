# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 16:51:50 2021

@author: mfratki
"""
#standard imports
from copy import deepcopy
import subprocess
#non-standard imports
import pandas as pd
import numpy as np
from pathlib import Path

#My packages
from hspf.hspfModel import hspfModel
from hspf.wdm import wdmInterface
from hspf import helpers
from mpcaHydro import data_manager as dm
from pyhcal import metrics
from pyhcal import figures
from pyhcal import setup_utils


def new_calibration(project_folder,model_name,download_station_data = True,run_model = True,convert_wdms = True):
    return setup_utils.create_calibration_project(model_name,project_folder,download_station_data,run_model,convert_wdms)


def load(project_folder):
    validate_project_folder(project_folder)
    return calibrator(project_folder)

def validate_project_folder(project_folder):
    project_path = Path(project_folder)
    assert project_path.exists(), 'Project folder does not exist'
    assert project_path.joinpath('model').exists(), 'Model folder does not exist'
    assert project_path.joinpath('data').exists(), 'Data folder does not exist'
    assert project_path.joinpath('output').exists(), 'Output folder does not exist'
    assert project_path.joinpath('targets.csv').exists(), 'targets.csv file does not exist in project folder'
    return True
 
class calibrator:
    def __init__(self,project_folder):
        self.project_path = Path(project_folder)
        self.project_name = self.project_path.name
        self.model_path = self.project_path.joinpath('model')
        self.output_path = self.project_path.joinpath('output')
        self.run = None
        self.start_date = '1996-01-01'
        self.end_date = '2100-01-01'
        
        # Load observational data into memory TODO: Convert to database?
        self.dm = dm.dataManager(self.project_path.joinpath('data'))
     
        self.targets = None
        if self.project_path.joinpath('targets.csv').exists():
            self.targets = pd.read_csv(self.project_path.joinpath('targets.csv'))  
              
        self.MODL_DB = pd.read_csv(self.project_path.joinpath('_'.join([self.project_name ,'MODL_DB.csv'])))
        
        self.model = None
        self._wdms = None
        self.uci = None
        
    ## Input/Output methods
    def initialize(self,reach_ids,default = 4):

        self.uci.update_table(default,'RCHRES','BINARY-INFO',0,columns = ['HEATPR','HYDRPR','SEDPR','OXRXPR','NUTRPR','PLNKPR'],operator = 'set')
        self.uci.update_table(2,'RCHRES','BINARY-INFO',0,columns = ['HEATPR','HYDRPR','SEDPR','OXRXPR','NUTRPR','PLNKPR'],opnids = reach_ids,operator = 'set')
        
        self.uci.write(self.model.uci_file)
        winHSPF = str(Path(__file__).resolve().parent.parent) + '\\bin\\WinHSPFLt\\WinHspfLt.exe'     
        subprocess.run([winHSPF,self.model.uci_file]) #, stdout=subprocess.PIPE, creationflags=0x08000000)
        
    def set_dates(self, start_date = '1996-01-01',end_date ='2100-01-01'):
        self.start_date = start_date
        self.end_date = end_date

        
    def load_model(self,name):

        if isinstance(name,int): # Default approach
            self.run = name
            name = '_'.join([self.project_name , str(name)])   
        else:
            name = str(name)
            self.run = None
            
        self.model = hspfModel(self.model_path.joinpath(name + '.uci'))  
        
        # WDM data never changes so I am trying to avoid reloading it each time the model is updated.
        # Very brittle solution. TODO: think harder about how to handle this.
        if self._wdms is None:
            try:
                self._wdms = wdmInterface(self.model.wdm_paths)
            except:
                pass
                
        self.model.wdms = self._wdms
        self.model.reports.wdms = self._wdms
        self.uci = deepcopy(self.model.uci) #uci to be manipulated 


    def run_model(self,name = None,overwrite_hbn = False): # NO STATE CHANGE 
        
        if name is None:
            name = '_'.join([self.project_name, str(self.run+1)])   
        elif isinstance(name,int): # Default approach
             name = '_'.join([self.project_name , str(name)])  
        else:
            name = str(name) 
        
        if not overwrite_hbn:
            self.uci.update_bino(name)
        
        uci_file = self.model_path.joinpath(name + '.uci').as_posix()        
        self.uci.write(uci_file)
        #winHSPF = str(Path(__file__).resolve().parent.parent) + '\\bin\\WinHSPFLt\\WinHspfLt.exe'     
        subprocess.run([self.model.winHSPF,uci_file]) #, stdout=subprocess.PIPE, creationflags=0x08000000)
    

    def get_simulated_output(self,reach_ids,constituent,time_step = 'YE'):
        sim = self.model.hbns.get_reach_constituent(constituent,reach_ids,time_step)
        sim.name = 'simulated'
        return sim
    
    def get_observed_data(self,station_ids,constituent,time_step = 'YE',baseflow_percentage = None):
        obs = self.dm._get_data(station_ids,constituent,agg_period = time_step).sort_index(level = 'index')
        obs.name = 'observed'
        return obs
     
    
    def compare_simulated_observed(self,station_ids,reach_ids,constituent,time_step,flow_station_ids = None, dropna = False, baseflow_percentage = None):
        obs = self.get_observed_data(station_ids,constituent,time_step)
        sim = self.get_simulated_output(reach_ids,constituent,time_step = time_step)
        
        #Joing observed and simulated 
        df = sim.join(obs,how = 'outer')
        df = df.loc[(df.index >= obs.index.min()) & (df.index <= obs.index.max())]
        if dropna: df = df.dropna()
        df.columns = ['simulated','observed']
        
        if flow_station_ids is None: flow_station_ids = station_ids
        
        
        # matching flow data
        sim_flow = self.get_simulated_output(reach_ids,'Q',time_step)
        sim_flow.name = 'simulated_flow'
        sim_flow.columns = ['simulated_flow']
        df = df.join(sim_flow,how = 'inner')
        obs_flow = self.get_observed_data(flow_station_ids,'Q',time_step)
        obs_flow.name = 'observed_flow'
        obs_flow.columns = ['observed_flow']
        df = df.join(obs_flow,how='left')

        obs_baseflow = self.get_observed_data(flow_station_ids,'QB',time_step)
        obs_baseflow.name = 'observed_baseflow'
        obs_baseflow.columns = ['observed_baseflow']
        df = df.join(obs_baseflow,how='left')
        df.columns = ['simulated','observed','simulated_flow','observed_flow','observed_baseflow']
        
        if baseflow_percentage is not None:
            df = df.loc[(df['observed_baseflow']/df['observed_flow'] >= baseflow_percentage/100)]
        
        # Add metadata
        df.attrs['station_ids'] = station_ids
        df.attrs['reach_ids'] = reach_ids
        df.attrs['constituent'] = constituent
        df.attrs['unit'] = obs.attrs['unit']
        df.attrs['time_step'] = time_step
        df.attrs['flow_station_ids'] = flow_station_ids
        return df
    
    
    
    
    def compare_wplmn(self,station_ids,reach_ids,constituent,unit,flow_station_ids = None,sample=True):
        obs = pd.concat([self.dm.get_wplmn_data(station_id,constituent,unit,'D',samples_only=sample) for station_id in station_ids])
        #sim = self.get_simulated_output(reach_ids,constituent,time_step = 'D',unit = unit)


        if (constituent == 'TSS') & (unit == 'lb'): #convert TSS from lbs to us tons
                obs.loc[:,'value'] = obs.loc[:,'value']/2000
        
        sim = self.model.hbns.get_rchres_data(constituent,reach_ids, unit,'D')

        df = sim.join(obs,how = 'outer')
        df.columns = ['simulated','observed']

        


        
        sim_flow = self.get_simulated_output(reach_ids,'Q','D')
        sim_flow.name = 'simulated_flow'
        df = df.join(sim_flow,how = 'inner')
        if flow_station_ids is None:
            # If wplmn station has flow data use it otherwise use the specifiec wiski station ids
        # matching flow data
            obs_flow = pd.concat([self.dm.get_wplmn_data(station_id,'Q',unit,'D',samples_only=sample) for station_id in station_ids])
        else:
            obs_flow = self.get_observed_data(flow_station_ids,'Q','D')
        
        obs_flow.name = 'observed_flow'
        df = df.join(obs_flow,how='left')
        df.columns = ['simulated','observed','simulated_flow','observed_flow']
        # Add metadata
        df.attrs['station_ids'] = station_ids
        df.attrs['reach_ids'] = reach_ids
        df.attrs['constituent'] = constituent
        df.attrs['unit'] = obs.attrs['unit']
        df.attrs['time_step'] = 'D'
        df.attrs['flow_station_ids'] = station_ids
        return df



# Objective Functions sort of

    def aggregate(self,station_ids,reach_ids,constituent,units,time_step,agg_func = 'mean'):
        df = self.compare_simulated_observed(station_ids, reach_ids, constituent, units, time_step)
        
        period = 'M'
        
        if period == 'M':
            grouper = df.index.month
        if period == 'Y':
            grouper = df.index.year
        if period == 'W':
            grouper = df.index.week
        if period == 'D':
            grouper = df.index.dayofyear
        
        df_agg = pd.DataFrame(np.ones((12,3))*np.nan,index = range(1,13),columns = ['simulated','observed','ratio'])
        df_agg.index.name = 'month'
        df = df.groupby(grouper).agg(agg_func)[['simulated','observed']]
        df.columns = ['simulated','observed']
        df['ratio'] = df['observed']/df['simulated']
        df_agg.loc[df.index,df.columns] = df.values
        
        df_agg.loc['Mean'] = df_agg.agg('mean')
        df_agg['ratio'] = df_agg['observed']/df_agg['simulated']

        return df_agg

    def landcover(self,constituent,ref_landcover = None):
        def normalize_group(group, ref_landcover):
            if ref_landcover in group['LSID'].to_list():
                ref_value = group.loc[group['LSID'] == ref_landcover, 'mean'].values[0]
                group['mean_norm'] = group['mean'] / ref_value
            else:
                group['mean_norm'] = pd.NA
            return group

        if ref_landcover is None:
            ref_landcover = self.targets['uci_name'][self.targets['dom_lc']==1].values[0]

        df = self.model.hbns.get_perlnd_data(constituent)*2000 #tons/ac/yr to lbs/acr/year
        df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
        df = df.mean().rename('mean').to_frame()
        df = pd.merge(df, self.uci.opnid_dict['PERLND'], left_index = True,right_on='TOPFST', how='inner')
        df_normalized = pd.concat([normalize_group(group, ref_landcover) for _, group in list(df.groupby('metzone'))])
        
        targets = self.targets.set_index('uci_name')[constituent]
        targets = targets/targets.loc[ref_landcover]
        
        df_normalized['target'] = targets.loc[df_normalized['LSID']].values/df_normalized['mean_norm']
        df_normalized = df_normalized.fillna(1) #don't make any changes to 0 concentration perlands
        #df_normalized = df_normalized.join(self.uci.table('PERLND','SED-PARM3'))
        return df_normalized



    def landcover_legacy(self,constituent):
        perlnd_names = self.model.uci.table('PERLND','GEN-INFO')['LSID']
        df = self.model.hbns.get_perlnd_data(constituent)*2000 #tons/ac/yr to lbs/acr/year
        df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
        
        # if self.model.uci.LSID_flag == 1:
        #     print('LSID Error')
        #     return
        
        perland_dict = self.model.uci.opnid_dict['PERLND']
        
        
        dom_lc = int( self.targets['lc_number'][ self.targets['dom_lc'] == 1] )

        df_mean_norm = normalize_mean(df,perland_dict,dom_lc)
        df_mean_norm.loc[df_mean_norm.mean_norm ==0,'mean_norm'] = np.nan
        targets = self.targets.set_index('lc_number')[constituent]
        targets = targets/targets.loc[dom_lc]
        
        df_mean_norm['target'] = targets.loc[df_mean_norm['landcover']].values/df_mean_norm['mean_norm']
        df_mean_norm = df_mean_norm.replace(np.nan,1) #don't make any changes to 0 concentration perlands
        df_mean_norm['uci_name'] = perlnd_names.loc[df_mean_norm.index]
        return df_mean_norm
    
    
    def scour(self,target):     
        # Erosivity adjustment only
        assert((target > 0) & (target < 1))
        scour  = self.model.reports.scour_report()
        #TODO: add check for this
        # Assume all nonpoint values are greater than 0...
        # if depscour is greater than 0
        target = scour['nonpoint']*(1-target)/target # Assuming nonpoint load is set
        adjustment = np.abs(scour['depscour'])/target
        adjustment[(adjustment < 1.05) & (adjustment > .95)] = 1 # Don't change reaches where the depscour is close to the target
        adjustment[adjustment > 1.05] = .95 # Since depscour is negative we have to swap this. I think if I do target/depscour this line would be less confusing
        adjustment[adjustment < .95] = 1.05
        adjustment[scour['depscour'] > 0] = 2 # Double any values where the depscour is positive
        adjustment[scour['LKFG'] == 1] = 1  # Ignore lake flags
        adjustment[np.isnan(adjustment)] = 1
        
        return adjustment

    
    # Methods for updating table values
    def update_table(self,value,operation,table_name,table_id,opnids = None,columns = None,operator = '*',axis = 0):
        self.uci.update_table(value,operation,table_name,table_id,opnids,columns,operator,axis)

    def get_adjustments(self,station_ids,reach_ids, constituent,method):
        
        if method == 'landcover':
            adjustment = self.landcover(constituent)['target'] #pandas series #by opnid
            axis = 0
        elif method =='load': #monthly
            adjustment = self.aggregate(station_ids,reach_ids, constituent,'lb','D',agg_func = 'sum')['ratio'].iloc[0:12] #pandas series by column
            axis = 1
        elif method == 'conc':
            adjustment = self.aggregate(station_ids,reach_ids, constituent,'mg/l','D')['ratio'].iloc[0:12] #pandas series by column
            axis = 1

        else:
            print('Not a valid method')
        return adjustment,axis #ouput dataframe with index representing the opnid


    def update_kser(self,station_ids,reach_ids, constituent,method,opnids = None):   
        #TODO account for the additional comment column
        assert method in ['load','landcover']
        
        adjustment,axis = self.get_adjustments(station_ids,reach_ids, constituent,method)
        if (method == 'landcover') & (opnids is None):
            opnids = adjustment.index.intersection(self.uci.table('PERLND','SED-PARM3',0).index)
                
        self.update_table(adjustment,'PERLND','SED-PARM3', 0,opnids,['KSER'], '*',axis)
 
    
    def update_qualprop(self,station_ids,reach_ids, constituent,method,table_name, opnids = None, months = [1,2,3,4,5,6,7,8,9,10,11,12],threshold = 0, max_change = 1000, update_alg = '*'):
        assert method in ['conc','load','landcover']
        assert table_name in ['MON-IFLW-CONC','MON-GRND-CONC']
        assert max_change >= threshold
        
       
        
        threshold = threshold/100
        max_change = max_change/100
        
        table_id = {'N':1,
                    'TKN':0,
                    'OP':2,
                    'TP':3}[constituent]
                    #nutrient_id-1 # Shift as tables in the uci dictionary are stored starting at the 0 index
        
        adjustment,axis = self.get_adjustments(station_ids,reach_ids, constituent,method)
        if opnids is None:
            opnids = adjustment.index.intersection(self.uci.table('PERLND',table_name,table_id).index)
        
        if method == 'load':
            adjustment = adjustment.loc[months]
        
        if method == 'landcover':
            adjustment = adjustment.loc[opnids]
  
    
        # Apply threshold adjustment
        adjustment[np.isnan(adjustment)] = 1
        adjustment[np.abs((adjustment-1)) <= threshold] = 1 # don't change values below threshold
        direction = np.sign(adjustment - 1)[np.abs(adjustment - 1) > max_change]
        adjustment[np.abs(adjustment-1) > max_change] = 1+ direction*max_change # Formla assumes it is flux/model
        #Note that in uci.update_table() there is further screening to account for adjustments below the model precision
        
        #column_prefix = self.uci.get_table_info('PERLND',table_name)['NAME'].str[:3].iloc[1]
        months = np.array(months)
        column_prefix = self.uci.table('PERLND',table_name,table_id).columns.str[:3][0]
        columns = [column_prefix+helpers.get_months(month) for month in months]
        
        self.uci.update_table(adjustment.values,'PERLND',table_name,table_id,opnids,columns,update_alg,axis)
        
    def update_erosivity(self, opnids = None):
        adjustment,axis = self.get_adjustments(0,'scour')
        
        table = self.uci.table('RCHRES','SILT-CLAY-PM',0)
        
        if opnids is None:
            opnids = adjustment.index.intersection(table.index)
        
        self.update_table(adjustment,'RCHRES','SILT-CLAY-PM', 0,opnids,'M','*',axis)
        self.update_table(adjustment,'RCHRES','SILT-CLAY-PM', 1,opnids,'M','*',axis)

    
    def save_output(self, constituent,station_ids,reach_ids,time_step = 'D',flow_station_ids=None,drng_area = None,save_path = None,start_year = 1996, end_year = 2100):
        if save_path is None:
            save_path = self.output_path
        if drng_area is None:
            drng_area = self.uci.network.drainage_area(reach_ids)
            #drng_area = sum([self.uci.network.drainage_area(reach_id) for reach_id in reach_ids])        
        
        run_number = self.run
        
        if flow_station_ids is None:
            flow_station_ids = station_ids
            
        if constituent == 'Q':
            constituent = 'Q'
            units = 'cfs'
            df = self.compare_simulated_observed(flow_station_ids,reach_ids,constituent,
                                                time_step = time_step)
    
    
    
            #TODO: Move the exporting of these tables into the report module to decouple things
            metrics.hydro_stats(df.dropna(),drng_area).to_csv(save_path.joinpath(f'hydrostats_{station_ids}'))
            self.model.reports.annual_water_budget('PERLND').to_csv(save_path.joinpath(f'{station_ids}_annual_perlnd_water_budget.csv'))
            self.model.reports.annual_water_budget('IMPLND').to_csv(save_path.joinpath(f'{station_ids}_annual_implnd_water_budget.csv'))
            self.model.reports.annual_water_budget('RCHRES').to_csv(save_path.joinpath(f'{station_ids}_annual_perlnd_rchres_budget.csv'))
            self.model.reports.ann_avg_watershed_loading(constituent,reach_ids).to_csv(save_path.joinpath('annual_runoff.csv'))
            #self.model.reports.monthly_runoff().to_csv(save_path.joinpath('monthly_runoff.csv'))

            
           #self.model.reports.avg_ann_yield('Q',reach_ids).to_csv(save_path.joinpath(f'{station_ids}_avg_ann_outflows.csv'))
            #self.model.reports.avg_monthly_outflow().to_csv(save_path.joinpath(f'{station_ids}_avg_monthly_outflows.csv'))
            
            figures.contTimeseries(df,station_ids,constituent,units,save_path)
            figures.FDCexceed(df.dropna(),station_ids,constituent,units,save_path)
            figures.scatter(df.dropna(),station_ids,constituent,units,save_path)
            figures.monthly_bar(metrics.monthly(df.dropna(),units),station_ids,constituent,units,save_path)
        
        else:
            assert constituent in ['TSS','TP','OP','N','TKN']
            df= self.compare_simulated_observed(
                station_ids,
                reach_ids,
                constituent,
                time_step,
                flow_station_ids = flow_station_ids)
            
            if df.empty:
                print(f'No Observation Data found for {constituent} at {station_ids}')
                return
            reachid_str = '_'.join([str(reach_id) for reach_id in reach_ids])

            figures.timeseries(df,station_ids,constituent,'mg/l',save_path = save_path.joinpath(f'{constituent}_Timeseries_{reachid_str}_{run_number}.png'))
            
            
            df =df.loc[(df.index.year >= start_year) & (df.index.year <= end_year)]

            stats = metrics.stats(df.dropna(subset=['observed']),'mg/l')[['observed','simulated','per_error','abs_error']]
            stats.to_csv(save_path.joinpath(f'{constituent}_stats_{reachid_str}_{run_number}.csv'))
        
            figures.scatter(df.dropna(subset=['observed']),station_ids,constituent,'mg/l',save_path.joinpath(f'{constituent}_Scatter_{reachid_str}_{run_number}.png'))
            figures.FDCexceed(df.dropna(subset=['observed']),station_ids,constituent,'mg/l',save_path.joinpath(f'{constituent}_Exceedence_{reachid_str}_{run_number}.png')) 
            figures.timeseries(df,station_ids,constituent,'mg/l',save_path.joinpath(f'{constituent}_Timeseries_{reachid_str}_{run_number}.png'))
            
            if len(df.dropna(subset = ['observed','observed_flow'])) > 10:    
                figures.rating(df.dropna(subset = ['observed','observed_flow']),station_ids,constituent,'mg/l',save_path.joinpath(f'{constituent}_Rating_{reachid_str}_{run_number}.png'))
                figures.LDC(df.dropna(subset = ['observed','observed_flow']),station_ids,constituent,'mg/l',time_step = time_step, save_path = save_path.joinpath(f'{constituent}_LDC_{reachid_str}_{run_number}.png'))

            
            

def chuck(adjustment,table):
    # If increasing monthly concentration increase the minimum concnetration value of Mi and Mi+1
    # If decreasing monthly concentration decrease the maximum concnetration value of Mi and Mi+1
    # If concnetration values are equal increase both equally
    table['dummy'] = table.iloc[:,0]
    zero_table = table.copy()*0
    count_table = zero_table.copy()
    for index, value in enumerate(adjustment[0]):
            next_index = index+1             
            if value > 1:
                for row,(a,b) in enumerate(zip(table.iloc[:,index].values, table.iloc[:,next_index].values)):
                    zero_table.iloc[row,index+np.nanargmin([a,b])] += np.nanmin([a,b])*value
                    count_table.iloc[row,index+np.nanargmin([a,b])] += 1
            elif value < 1:
                for row,(a,b) in enumerate(zip(table.iloc[:,index].values, table.iloc[:,next_index].values)):
                    zero_table.iloc[row,index+np.nanargmax([a,b])] += np.nanmax([a,b])*value
                    count_table.iloc[row,index+np.nanargmax([a,b])] += 1
    
    
    zero_table.drop('dummy',axis=1,inplace=True)
    count_table.drop('dummy',axis=1,inplace=True)
    
    zero_table[count_table == 0] = table[count_table==0]
    count_table[count_table == 0] = 1
    zero_table = zero_table/count_table
    return zero_table       

def normalize_mean(df,perland_dict,dom_lc):
     df_mean = df.mean().rename('mean').to_frame()
     df_mean['mean_norm'] = df_mean['mean'].values
     
     perlands = df_mean.index
     perland_dict['landcover_group'] = (perland_dict['landcover'] == perland_dict['landcover'].iloc[0]).cumsum()
     
     metzones = np.array([perland_dict.loc[perland,'metzone'] for perland in perlands])
     landcover = np.array([perland_dict.loc[perland,'landcover'] for perland in perlands])
     landcover_groups = np.array([perland_dict.loc[perland,'landcover_group'] for perland in perlands])

     for group in np.unique(landcover_groups):
         dom_perlnd = perland_dict.index[(perland_dict['landcover_group'] == group) & (perland_dict['landcover'] == dom_lc)]
         df_mean.loc[landcover_groups == group,'mean_norm'] = df_mean.loc[landcover_groups == group,'mean_norm']/df_mean.loc[dom_perlnd,'mean_norm'].values
         
     df_mean['metzones'] = metzones
     df_mean['landcover'] = landcover
     df_mean['perlands'] = perlands
     df_mean.sort_values(by = ['metzones','perlands'],inplace = True)
     return df_mean


# def column_prefix():
#     months = np.array(months)
#     column_prefix = self.uci.table('PERLND',table_name,table_id).columns.str[:3][0]
#     columns = [column_prefix+ch.get_months(month) for month in months]

def threshold(adjustment,threshold,max_change):
    # Apply threshold adjustment
    adjustment[np.isnan(adjustment)] = 1
    adjustment[np.abs((adjustment-1)) <= threshold] = 1 # don't change values below threshold
    direction = np.sign(adjustment - 1)[np.abs(adjustment - 1) > max_change]
    adjustment[np.abs(adjustment-1) > max_change] = 1+ direction*max_change # Formla assumes it is flux/model
    #Note that in uci.update_table() there is further screening to account for adjustments below the model precision
    return adjustment  


#class hydrologyCalibrator(calibrator):
    
#class nutrientCalibrator(calibrator):
        
class sedimentCalibrator(calibrator):
    
    def update_kser(self,method,opnid = None):   
        #TODO account for the additional comment column
        assert method in ['load','landcover','sftl']
        
        table = self.uci.table('PERLND','SED-PARM3',0,False)
        
        
        if method == 'load':
            adjustment = self.compare(0,aggregate = True).loc['Mean']['ratio']      
        elif method == 'landcover':
            adjustment = self.landcover(0)['target']
            table = self.uci.table('PERLND','SED-PARM3',0)
            if opnid == None:
                opnid = table.index
            adjustment = np.array(adjustment.loc[opnid])[:,None]
        elif method == 'sftl':
            adjustment = self.sftl()
        
        self.uci.replace_table('PERLND','SED-PARM3',0)
    
    def update_erosivity(self,param = 'M',opnid = None,update_alg = '*'):
        adjustment = self.scour()  
        table = self.uci.table('RCHRES','SILT-CLAY-PM',0)
        if opnid == None:
            opnid = table.index
        adjustment = np.array(adjustment.loc[opnid])[:,None]
        self.uci.update_table(adjustment,'RCHRES','SILT-CLAY-PM',table_id = 0,opnid = opnid,columns = [param],update_alg = update_alg)
        
        adjustment = self.scour()
        adjustment = np.array(adjustment.loc[opnid])[:,None]
        self.uci.update_table(adjustment,'RCHRES','SILT-CLAY-PM',table_id = 1,opnid = opnid,columns = [param],update_alg = update_alg) 
    
        
    def fit_param(self,param,m_factor,N = 2,opnid = None,run = None):
        bounds = {'M':[.000000001,.01,2,5], #maxlow,low,high,maxhigh
                  'TAUCD':[.001,.01,.3,1],
                  'TAUCS':[.01,.05,.5,3]}
        if run == None:
            run = self.run
        
        data = self.load_data('scour',N=10000)
        data = data.loc[:,range(run-N+1,run+1),:]
    
        if opnid == None:
            opnid = data.reset_index(level=[1]).index.unique() # assumes multiindex
        
        for index in opnid:
            if any(data.loc[index]['LKFG'] == 0):
                x = data.loc[index]['depscour']
                y = data.loc[index][param]
                linear_model=np.polyfit(x,y,1)
                linear_model_fn=np.poly1d(linear_model)
                m = linear_model_fn(-data.loc[index]['nonpoint'].iloc[1]*.25)
                if m < bounds[param][0]:
                    m = bounds[param][0]
                if m > bounds[param][3]:
                    m = bounds[param][3]
                self.update_table('RCHRES','SILT-CLAY-PM',0,m,'set',opnid = index,columns = [param]) #mod.update_table(operation,table_name,table_id,adjustment,operator,opnids,columns)
                self.update_table('RCHRES','SILT-CLAY-PM',1,m*m_factor,'set',opnid = index,columns = [param]) #mod.update_table(operation,table_name,table_id,adjustment,operator,opnids,columns)
    
    def erosivity(self,m_factor,param = 'M',opnid = None,run = None,iterations = 1):
        
        if run == None:
            run = self.run
        
        # run model updating erosivity for N iterations
        for iteration in range(iterations):
            self.update_erosivity(param = param,opnid = opnid)
            self.run_model() # creates the run+1 uci file and runs it using WinHspfLT
            run = run + 1
            self.load_model(run)
            self.save_data()
     
    
        self.fit_param(param,m_factor,iterations+1,opnid,run)
        self.run_model() # creates the run+1 uci file and runs it using WinHspfLT
        
        run = run + 1
        self.load_model(run)
        self.save_data()

    def scour(hbn,uci):     
        # Erosivity adjustment only
        scour  = reports.scour_report(hbn,uci)
        #TODO: add check for this
        # Assume all nonpoint values are greater than 0...
        # if depscour is greater than 0
        target = scour['nonpoint']*.25 # Assuming nonpoint load is set
        adjustment = np.abs(scour['depscour'])/target
        adjustment[(adjustment < 1.05) & (adjustment > .95)] = 1 # Don't change reaches where the depscour is close to the target
        adjustment[adjustment > 1.05] = .95 # Since depscour is negative we have to swap this. I think if I do target/depscour this line would be less confusing
        adjustment[adjustment < .95] = 1.05
        adjustment[scour['depscour'] > 0] = 2 # Double any values where the depscour is positive
        adjustment[scour['LKFG'] == 1] = 1  # Ignore lake flags
        adjustment[np.isnan(adjustment)] = 1
        
        return adjustment


    
