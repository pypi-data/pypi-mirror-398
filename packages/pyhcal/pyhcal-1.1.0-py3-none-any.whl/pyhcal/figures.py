# -*- coding: utf-8 -*-
"""
Created on Wed May  8 09:40:51 2024

@author: cfreema
"""

#%% Add libraries

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.stats import pearsonr
from pathlib import Path


#%% Minnesota Color Scheme and Font

# Minnesota Brand Colors
COLORS = {'Minnesota Blue': '#003865',
          'Minnesota Green': '#78BE21',
          'White': '#FFFFFF',
          'Black': '000000',
          'Accent Teal': '#008EAA',
          'Accent Green': '#0D5257',
          'Accent Orange': '#8D3F2B',
          'Accent Purple': '#5D295F',
          'Extended Accent Blue Gray': '#A4BCC2',
          'Extended Accent Cream': '#F5E1A4',
          'Extended Accent Sky Blue': '#9BCBEB',
          'Extended Accent Gold': '#FFC845',
          'Dark Gray': '#53565A',
          'Medium Gray': '#97999B',
          'Light Gray': '#D9D9D6',
          'Orange': '#E57200'}

# Minnesota Substitute Typography
CFONT = {'fontname': 'Calibri'}

#%% Monthly Bar Plot
def monthly_bar(df, station_id, constituent, units, save_path=None, yaxis=None, ylimit=None):
    '''
    Returns a timeseries plot of hourly simulated concentrations and observed concentrations 
    with the same date range as the input data (df). The hourly simulated concentrations are 
    represented with a line and the observed concentrations are represented with points.

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 2 columns: simulated, observed.
        -The dates must be in the datetime Python format.
        -The date range must already be filtered to the date range you wish to plot in the 
         figure and should be on an hourly timestep.
        -The hourly simulated concentrations must be paired with observed concentrations, where 
         grab samples exist.
        -If you wish to plot concentrations from more than one station, there should still only be one 
         'obs' column, i.e., no stations overlapping in dates.
        -In pre-processing, the time of the observed samples may need to be adjusted to the nearest 
         top of the hour in order to merge the observed data with the simulated data.
        
    station_id : Python list
        -Include one or more station ID numbers (i.e., H49009001).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis
        -Options include: 
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen) 
            
    units: Python string
        -Input units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
   
            
    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_timeseries_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'
    
    yaxis: Python string
        -Options: None, log, Log
        -Default is None and will create a plot with a linear y-axis.
        -yaxis = log (or Log) will create a plot with a log y-axis.
        -Use log when you have a dataset with a high range of concentrations (i.e. TSS).
        
    ylimit: integer
        -Insert a value that will be the upper limit of the y-axis (e.g. ylimit = 400)
        -Default is None and will use the dataset to set the y-axis limits.

    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    
    units = df.attrs['unit']
    
    assert units in ['mg/l','lb','cfs']
    
    if units in ['cfs','mg/l']:
        df = df[['observed','simulated']].groupby(df.index.month).mean()
    else:
        df = df[['observed','simulated']].groupby(df.index.month).sum()

    
    # cf2cfs = {'hourly':3600,
    #           'daily':86400,
    #           'monthly':2592000,
    #           'yearly':31536000,
    #           'h':3600,
    #           'D':86400,
    #           'M':2592000,
    #           'Y':31536000}
    
    # if units == 'mg/l':
    #     df['simulated'] = 2.20462e-6*df['simulated']/0.0353147*df['simulated_flow']*cf2cfs[time_step]
    #     df['observed'] = 2.20462e-6*df['observed']/0.0353147*df['observed_flow']*cf2cfs[time_step]
    #     units = 'lb'
    
    
    
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)
    # months = {1:'JAN', 2:'FEB', 3:'MAR', 4:'APR', 5:'MAY', 6:'JUN', 7:'JUL',
    #        8:'AUG', 9:'SEP', 10:'OCT', 11:'NOV', 12:'DEC'}
    
    
    
    #index = ['January','Febuary','March','April','May','June','July','August','September','October','November','December']
    df[['observed','simulated']].plot.bar(ax=ax,color = {'simulated':COLORS.get('Orange'),'observed':COLORS.get('Minnesota Blue')})
    stations = ', '.join(station_id)
    plt.title(f'Simulated and Observed {constituent} \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    plt.xlabel('Month', **CFONT, fontsize = 10) 
    # Add y label
    plt.ylabel(f'{constituent} ({units})', **CFONT, fontsize = 10) 
    # Add legend
    plt.legend(['Observed', 'Simulated'], fontsize = 9)
    # Set legend font to Calibri
    L = ax.legend()
    plt.setp(L.texts, family = 'Calibri')
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    
    #Axis settings depending on user input
    if yaxis == 'log' or yaxis == 'Log':
        # Convert y axis to log scale
        plt.yscale('log')
        # Add axis gridlines
        plt.grid(which='major', axis='y', linewidth=0.3)
        plt.grid(which='minor', axis='y', linewidth=0.3)
        
    else:
        # Add y axis gridlines and set the y axis minimum to 0
        ax.set_axisbelow(True)
        plt.grid(which='major', axis='y', linewidth=0.3)
        plt.ylim(bottom=0)
        
    if ylimit is not None:
        # Define the upper limit of the y-axis based on user input
        plt.ylim(top = ylimit)
    
    # Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_monthly_bar' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')
    
    return fig, ax

#%% Timeseries
def timeseries(df, station_id, constituent, units, save_path=None, yaxis=None, ylimit=None):
    '''
    Returns a timeseries plot of hourly simulated concentrations and observed concentrations 
    with the same date range as the input data (df). The hourly simulated concentrations are 
    represented with a line and the observed concentrations are represented with points.

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 2 columns: simulated, observed.
        -The dates must be in the datetime Python format.
        -The date range must already be filtered to the date range you wish to plot in the 
         figure and should be on an hourly timestep.
        -The hourly simulated concentrations must be paired with observed concentrations, where 
         grab samples exist.
        -If you wish to plot concentrations from more than one station, there should still only be one 
         'obs' column, i.e., no stations overlapping in dates.
        -In pre-processing, the time of the observed samples may need to be adjusted to the nearest 
         top of the hour in order to merge the observed data with the simulated data.
        
    station_id : Python list
        -Include one or more station ID numbers (i.e., H49009001).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis
        -Options include: 
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen) 
            
    units: Python string
        -Input units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
        -Options include:
            mg/L (milligrams per liter)
            ppm (parts per million)
            ug/L (micrograms per liter)
            ppb (parts per billion)
            
    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_timeseries_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'
    
    yaxis: Python string
        -Options: None, log, Log
        -Default is None and will create a plot with a linear y-axis.
        -yaxis = log (or Log) will create a plot with a log y-axis.
        -Use log when you have a dataset with a high range of concentrations (i.e. TSS).
        
    ylimit: integer
        -Insert a value that will be the upper limit of the y-axis (e.g. ylimit = 400)
        -Default is None and will use the dataset to set the y-axis limits.

    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)
    # Plot simulated TSS concentrations (line)
    sim, = ax.plot(df['simulated'], label = 'sim', color = COLORS.get('Orange'), linewidth = '0.9')  
    # Plot observed TSS concentrations (points)
    obs, = ax.plot(df['observed'], '*', mfc = 'none', label = 'obs', mec = COLORS.get('Minnesota Blue'))  
    # Add plot title
    stations = ', '.join(station_id)
    plt.title(f'Simulated and Observed {constituent} Concentrations \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    plt.xlabel('Date', **CFONT, fontsize = 10) 
    # Add y label
    plt.ylabel(f'{constituent} ({units})', **CFONT, fontsize = 10) 
    # Add legend
    plt.legend(handles=[sim, obs], fontsize = 9)
    # Set legend font to Calibri
    L = ax.legend()
    plt.setp(L.texts, family = 'Calibri')
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    
    #Axis settings depending on user input
    if yaxis == 'log' or yaxis == 'Log':
        # Convert y axis to log scale
        plt.yscale('log')
        # Add axis gridlines
        plt.grid(which='major', axis='y', linewidth=0.3)
        plt.grid(which='minor', axis='y', linewidth=0.3)
        
    else:
        # Add y axis gridlines and set the y axis minimum to 0
        plt.grid(which='major', axis='y', linewidth=0.3)
        plt.ylim(bottom=0)
        
    if ylimit is not None:
        # Define the upper limit of the y-axis based on user input
        plt.ylim(top = ylimit)
    
    # Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_timeseries_' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')
    
    return fig, ax

#%% Simulated versus Observed Concentrations Plot (Scatter): scatter

def scatter(df, station_id, constituent, units, save_path=None):
    '''
    Returns a scatter plot of simulated and observed concentrations. 
    A 1:1 fit indicates a perfect relationship between simulated and observed concentrations.

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 3 columns: sim, obs.
        -The simulated concentrations must be paired with observed concentrations, where grab samples exist.
        -If you wish to plot concentrations from more than one station, there should still only be one 
         'obs' column, i.e., no stations overlapping in dates.
        -In pre-processing, the time of the observed samples may need to be adjusted to the nearest top of 
         the hour in order to merge the observed data with the simulated data.
        
    station_id : Python list
        -Include one or more station ID numbers (i.e., H49009001).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis
        -Options include: 
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen)
            
    units: Python string
        -Input units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
        -Options include:
            mg/L (milligrams per liter)
            ppm (parts per million)
            ug/L (micrograms per liter)
            ppb (parts per billion)  
    
    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_scatter_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'

    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    # Calculate correlation coefficient
    corr, _ = pearsonr(df['observed'],df['simulated'])
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)
    # Plot observed versus simulated TSS concentrations (points)
    ax.plot(df['observed'], df['simulated'], 'o', alpha = 0.3, color = COLORS.get('Minnesota Green'))     
    # Add the correlation coefficient to the plot
    plt.text(0.1, 0.9, f'r = {corr:.2f}', transform=plt.gca().transAxes)
    # Add plot title
    stations = ', '.join(station_id)
    plt.title(f'Simulated versus Observed {constituent} Concentrations \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    plt.xlabel(f'Observed {constituent} ({units})', **CFONT, fontsize = 10) 
    # Add y label
    plt.ylabel(f'Simulated {constituent} ({units})', **CFONT, fontsize = 10) 
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    # Add y axis gridlines, set the x and y axis minimums to 0, and make the axes square
    plt.grid(which='major', axis='y', linewidth=0.3)
    plt.axis('square')
    plt.ylim(bottom=0)
    plt.xlim(left=0)
    
    # Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_scatter_' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')

    return fig, ax


#test_df = create_test_data()

#fig, ax = scatter(test_df,station_id, 'TSS', 'mg/L')


#%% Concentration vs Flow (Rating Curve): rating

def rating(df, station_id, constituent, units, save_path=None):
    '''
    Returns a concentration versus flow rating curve for both simulated and observed datasets. 

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 4 columns: simulated, simulated_flow, observed, observed_flow.
        -This function assumes the flow units are in cubic feet per second (cfs).
        -The simulated concentrations & flow must be paired with observed concentrations & flow.
        -If you wish to plot concentrations and flow from more than one station, there should 
         still only be one 'obs conc' column and one 'obs flow (cfs)' column
        -In pre-processing, the time of the observed samples and flow may need to be adjusted 
         to the nearest 15-minutes or nearest top of the hour in order to merge the observed data 
         with the simulated data.
        
    station_id : Python list
        -Include one or more station ID numbers (i.e., H49009001).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis
        -Options include: 
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen)   
        
    units: Python string
        -Input constituent units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
        -Options include:
            mg/L (milligrams per liter)
            ppm (parts per million)
            ug/L (micrograms per liter)
            ppb (parts per billion)  
            
    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_rating_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'
    
    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)
    # Plot observed concentration versus flow (points)
    obs, = ax.plot(df['observed_flow'], df['observed'], '*', label = 'obs', color = COLORS.get('Minnesota Blue'))     
    # Plot simulated concentration versus flow (points)
    sim, = ax.plot(df['simulated_flow'], df['simulated'], 'v', mfc = 'none', label = 'sim', mec = COLORS.get('Orange'))   
    # Add plot title
    stations = ', '.join(station_id)
    plt.title(f'Simulated and Observed {constituent} Concentration vs Flow \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    plt.xlabel('Flow (cfs)', **CFONT, fontsize = 10) 
    # Add y label
    plt.ylabel(f'{constituent} ({units})', **CFONT, fontsize = 10) 
    # Add legend
    plt.legend(handles=[obs, sim], fontsize = 9)
    # Set legend font to Calibri
    L = ax.legend()
    plt.setp(L.texts, family = 'Calibri')
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    # Convert x and y axis to log scale
    plt.yscale('log')
    plt.xscale('log')
    # Add axis gridlines
    plt.grid(which='major', axis='both', linewidth=0.3)
    
    # Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_rating_' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')

    return fig, ax


#test_df = create_test_data()

#fig, ax = rating(test_df,station_id, 'PO4', 'ug/L')

#%% Load Duration Curve: LDC

# # Create random data for input into LDC function
# def create_test_data():
#     start_date = datetime(2020,5,20)
#     end_date = datetime(2023,9,30)
#     date_range = ((end_date - start_date).days + 1)

#     random_days = np.random.randint(date_range, size=45)
#     obs_dates = pd.to_datetime(start_date) + pd.to_timedelta(random_days, unit='days')

#     test_df_obs = pd.DataFrame({'date' : obs_dates,
#                                 'obs load': np.random.randint(9000, size = 45).astype(float),
#                                 'obs flow': np.random.randint(1000, size = 45).astype(float)})

#     test_df_obs['obs rank'] = test_df_obs['obs flow'].rank(method = 'first', ascending = False)
#     test_df_obs['obs exceed %'] = test_df_obs['obs rank'] / (len(test_df_obs) + 1) * 100

#     sim_dates = pd.date_range(start='1/1/2020',end='12/31/2023')

#     test_df_sim = pd.DataFrame({'date' : sim_dates,
#                                 'sim load': np.random.randint(9000, size = 1461).astype(float),
#                                 'sim flow': np.random.randint(1000, size = 1461).astype(float)})

#     test_df_sim['sim rank'] = test_df_sim['sim flow'].rank(method = 'first', ascending = False)
#     test_df_sim['sim exceed %'] = test_df_sim['sim rank'] / (len(test_df_sim) + 1) * 100

#     test_df = test_df_sim.merge(test_df_obs, on = 'date', how = 'left')
    
#     return test_df


def LDC(df, station_id, constituent, units, time_step, save_path=None):
    '''
    Returns a load duration curve - constituent load versus flow exceedance percentage 
    for both simulated and observed datasets. 

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 5 columns: date, sim load, sim exceed %, obs load, obs exceed %.
        -Sim exceed % and obs exceed % represent flow exceedance (not load exceedance).
        -The entire modeled period of record may be used for the simulated data.
        -If you wish to use load and flow observational data from more than one station, there should 
          still only be one 'obs load' column and one 'obs exceed %' column.
        
    station_id : Python list
        -Include one or more station ID numbers (i.e., H49009001).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis
        -Options include: 
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen)  
            
    units: Python string
        -Input constituent units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
        -Options include:
            tons per day (tons/day)
            pounds per day (lb/day)

    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_LDC_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'

    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    assert units in ['mg/l','lb']
    
    cf2cfs = {'hourly':3600,
              'daily':86400,
              'monthly':2592000,
              'yearly':31536000,
              'h':3600,
              'D':86400,
              'M':2592000,
              'Y':31536000}
    
    if units == 'mg/l':
        df['simulated'] = 2.20462e-6*df['simulated']/0.0353147*df['simulated_flow']*cf2cfs[time_step]
        df['observed'] = 2.20462e-6*df['observed']/0.0353147*df['observed_flow']*cf2cfs[time_step]
        units = 'lb'
        
    df['simulated_flow rank'] = df['simulated_flow'].rank(method = 'average', ascending = False)
    df['simulated_flow exceed %'] = df['simulated_flow rank'] / (len(df) + 1) * 100
    df['observed_flow rank'] = df['observed_flow'].rank(method = 'average', ascending = False)
    df['observed_flow exceed %'] = df['observed_flow rank'] / (len(df) + 1) * 100

    
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)   
    # Plot simulated load versus flow exceedance (points)
    sim, = ax.plot(df['simulated_flow exceed %'], df['simulated'], 'v', mfc = 'none', label = 'sim', mec = COLORS.get('Orange'))
    # Plot observed load versus flow exceedance (points)
    obs, = ax.plot(df['observed_flow exceed %'], df['observed'], '*', label = 'obs', color = COLORS.get('Minnesota Blue'))  
    # Add plot title
    stations = ', '.join(station_id)
    plt.title(f'{constituent} Load Duration Curve \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    plt.xlabel('Flow Exceedance (%)', **CFONT, fontsize = 10) 
    # Add y label
    plt.ylabel(f'{constituent} ({units})', **CFONT, fontsize = 10) 
    # Add legend
    plt.legend(handles=[obs, sim], fontsize = 9)
    # Set legend font to Calibri
    L = ax.legend()
    plt.setp(L.texts, family = 'Calibri')
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    # Convert y axis to log scale
    plt.yscale('log')
    # Add axis gridlines
    plt.grid(which='major', axis='both', linewidth=0.3)
    plt.grid(which='minor', axis='y', linewidth=0.3)
    
    #Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_LDC_' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')

    return fig, ax

# #test_df = create_test_data()

# #fig, ax = LDC(test_df,station_id, 'OP', 'lbs/day')

#%% Timeseries Plot: contTimeseries

def contTimeseries(df, station_id, constituent, units, save_path=None):
    '''
    Returns a timeseries plot of simulated and observed continuous data with the same date range as
    the input data (df).

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 2 columns: observed, simulated
        -The dates must be in the datetime Python format.
        -The date range must already be filtered to the date range and timestep you wish to plot 
         in the figure.
        -Each simulated data point must have a corresponding observed data point. 
        -For TSS, N+N, PO4, TP, and TKN, the simulated data should be from HSPF and the observed data
         should be from FLUX (WPLMN).
        -The suggested units for each of the constituents are as follows:
                -flow: cubic feet per second (cfs)
                -temp: degrees Fahrenheit (ºF)
                -DO: milligrams per liter (mg/L)
                -TSS: kilograms per day (kg/d)
                -N+N: kilograms per day (kg/d)
                -PO4: kilograms per day (kg/d)
                -TP: kilograms per day (kg/d)
                -TKN: kilograms per day (kg/d)
        -If you wish to plot observed data from more than one station, there should still only be one 
         column for obs, i.e., no observed data overlapping in dates.
        
    station_id : Python list
        -Include one or more station ID numbers (i.e., ['H49009001', 'H25019002']).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis        
        -Options include: 
            Flow
            Temp (water temperature)
            DO (dissolved oxygen)
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen)
            
    units: Python string
        -Input units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
        -Options include:
            cfs
            ºF (degrees F)
            ºC (degrees C)
            mg/L (milligrams per liter)
            ppm (parts per million)
            kg/d (kilograms per day)

    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_contTimeseries_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'
        
    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)
    # Plot observed flow
    obs, = ax.plot(df['observed'], label = 'observed', color = COLORS.get('Minnesota Blue'), linewidth = '0.9')  
    # Plot simulated flow
    sim, = ax.plot(df['simulated'], label = 'simulated', color = COLORS.get('Orange'), linewidth = '0.5')  
    # Add plot title
    stations = ', '.join(station_id)
    plt.title(f'Simulated and Observed {constituent} \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    plt.xlabel('Date', **CFONT, fontsize = 10)   
    # Add y label
    plt.ylabel(f'{constituent} ({units})', **CFONT, fontsize = 10) 
    # Add legend
    plt.legend(handles=[obs, sim], fontsize = 9)
    # Set legend font to Calibri
    L = ax.legend()
    plt.setp(L.texts, family = 'Calibri')
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    # Add y axis gridlines and set the y axis minimum to 0
    plt.grid(which='major', axis='y', linewidth=0.3)
    plt.ylim(bottom=0)
    
    # Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_contTimeseries_' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')

    return fig, ax

#test_df = create_test_data()

#fig, ax = contTimeseries(test_df,station_id, 'Nitrate + Nitrite', 'kg/d')

#%% Duration Curve/Exceedance Plot: FDCexceed

# Create random data for input into FDCexceed function
def create_test_data():
    start_date = datetime(2020,5,20,8,0,0)
    end_date = datetime(2023,9,30,17,0,0)
    date_range = ((end_date - start_date).days + 1) * 24

    random_days = np.random.randint(date_range, size=80)
    dates = pd.to_datetime(start_date) + pd.to_timedelta(random_days, unit='hours')

    test_df_sim = pd.DataFrame({'date' : dates,
                                'sim': np.random.randint(500,size = 80).astype(float)})

    test_df_sim['simulated rank'] = test_df_sim['simulated'].rank(method = 'first', ascending = False)
    test_df_sim['simulated exceed %'] = test_df_sim['simulated rank'] / (len(test_df_sim) + 1) * 100

    test_df_obs = pd.DataFrame({'date' : dates,
                                'obs': np.random.randint(500,size = 80).astype(float)})

    test_df_obs['obs rank'] = test_df_obs['observed'].rank(method = 'first', ascending = False)
    test_df_obs['obs exceed %'] = test_df_obs['observed rank'] / (len(test_df_sim) + 1) * 100

    test_df = test_df_obs.merge(test_df_sim,on='date')
    
    return test_df

def FDCexceed(df, station_id, constituent, units, save_path=None):
    '''
    Returns a flow duration curve or exceedance plot for simulated and observed data.

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 2 columns: simulated, observed
        -In data preprocessing, the simulated data should be paired with observed data.
        -If you wish to use observed data from more than one station, there should still only be one 
         'obs' column, i.e., no overlapping observed data.
        -Exceedance percentage should be calculated by ranking data (highest is ranked #1), 
         then calculate exceedance percentage as follows:
            P = (m/n+1) * 100, where:
                P = exceedance percentage
                m = the ranking of all data for the period of record
                n = the total number of data points
                
    station_id : Python list
        -Include one or more station ID numbers (i.e., H49009001).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis
        -Options include: 
            Flow
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen)
            
    units: Python string
        -Input units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
        -Options include:
            cfs
            mg/L (milligrams per liter)
            ppm (parts per million)
            ug/L (micrograms per liter)
            ppb (parts per billion)
            
    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_FDCexceed_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'

    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    
    
    df['simulated rank'] = df['simulated'].rank(method = 'average', ascending = False)
    df['simulated exceed %'] = df['simulated rank'] / (len(df) + 1) * 100
    df['observed rank'] = df['observed'].rank(method = 'average', ascending = False)
    df['observed exceed %'] = df['observed rank'] / (len(df) + 1) * 100

    
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)
    # Sort obs in descending order, then plot observed FDC/exceedance plot
    df = df.sort_values(by = 'observed', ascending = False)
    obs, = ax.plot(df['observed exceed %'], df['observed'], label = 'observed', color = COLORS.get('Minnesota Blue'))  
    # Sort sim in descending order, then plot simulated FDC/exceedance plot
    df = df.sort_values(by = 'simulated', ascending = False)
    sim, = ax.plot(df['simulated exceed %'], df['simulated'], label = 'simulated', color = COLORS.get('Orange'))  
    # Add plot title
    stations = ', '.join(station_id)
    if constituent == 'Flow' or constituent == 'flow':
        plt.title('Flow Duration Curves \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    else: 
        plt.title(f'{constituent} Exceedance Plot \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    plt.xlabel('Exceedance Percentage', **CFONT, fontsize = 10) 
    # Add y label
    plt.ylabel(f'{constituent} ({units})', **CFONT, fontsize = 10) 
    # Add legend
    plt.legend(handles=[obs, sim], fontsize = 9)
    # Set legend font to Calibri
    L = ax.legend()
    plt.setp(L.texts, family = 'Calibri')
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    # Add axis gridlines
    plt.grid(which='major', axis='both', linewidth=0.3)
    plt.grid(which='minor', axis='y', linewidth=0.3)
    # Convert y axis to log scale
    plt.yscale('log')
    # Set the x axis minimum to 0
    plt.xlim(left=0)
    
    # Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_FDCexceed_' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')

    return fig, ax



#test_df = create_test_data()

#fig, ax = FDCexceed(test_df,station_id, 'flow', 'cfs')

#%% Flow Duration Curve or Exceedance Plot with Points: FDCexceedPoints

def FDCexceedPoints(df, station_id, constituent, units, save_path=None):
    '''
    Returns a duration curve (flow) or exceedance plot (sediment and nutrients)
    for observed data with points representing paired (not ranked) simulated data.

    Parameters
    ----------
    df : Pandas Dataframe
        -Dataframe with 2 columns: simulated, observed
        -In data preprocessing, the simulated data should be paired with observed data.
        -If you wish to use observed data from more than one station, there should still only be one 
         'obs' column, i.e., no overlapping observed data.
        -Exceedance percentage should be calculated by ranking data (highest is ranked #1), 
         then calculate exceedance percentage as follows:
            P = (m/n+1) * 100, where:
                P = exceedance percentage
                m = the ranking of all data for the period of record
                n = the total number of data points
                
    station_id : Python list
        -Include one or more station ID numbers (i.e., H49009001).
        -This argument is only used to include the station ID(s) in the plot title.
        -Example: ['H49009001'] or ['W49012002', 'W49012003']
        
    constituent: Python string
        -Input constituent as you'd like it to appear on the figure title and axis
        -Options include: 
            Flow
            TSS (total suspended solids)
            N+N (nitrate plus nitrite nitrogen)
            PO4 (orthophosphate phosphorus)
            TP (total phosphorus)
            TKN (total Kjeldahl nitrogen)
            
    units: Python string
        -Input units as you'd like it to appear on the figure axis (without parentheses)
        -Make sure the units you enter match the units of the data in your input df
        -Options include:
            cfs
            mg/L (milligrams per liter)
            ppm (parts per million)
            ug/L (micrograms per liter)
            ppb (parts per billion)
            
    save_path: Python string
        -Default is None and will not save the figure anywhere.
        -Enter the folder path OR the file path (it is recommended to save the file as a .png).
        -If a folder path is entered, the file name will default to 'constituent_FDCexceed_stationID(s)'
        -Make sure to use forward slashes (/) instead of backslashes (\).
        -File path example: 'C:/Users/cfreema/Desktop/delete/figure_6.png'
        -Folder path example: 'C:/Users/cfreema/Desktop/delete/'

    Returns
    -------
    fig : Figure object of matplotlib.figure module
    ax : AxesSubplot object of matplotlib.axes._subplots module

    '''
    
    df['observed rank'] = df['observed'].rank(method = 'first', ascending = False)
    df['observed exceed %'] = df['observed rank'] / (len(df) + 1) * 100

    
    # Create a figure containing a single axes
    fig, ax = plt.subplots(figsize = (7,4), dpi = 600)
    # Sort obs in descending order, then plot observed FDC/exceedance plot and paired sim conc
    df = df.sort_values(by = 'observed', ascending = False)
    sim, = ax.plot(df['observed exceed %'], df['simulated'], '.', label = 'simulated', color = COLORS.get('Orange'))  
    obs, = ax.plot(df['observed exceed %'], df['observed'], label = 'observed', color = COLORS.get('Minnesota Blue'))  
# START HERE 
    # Add plot title
    stations = ', '.join(station_id)
    if constituent == 'Flow' or constituent == 'flow':
        #plt.title('Flow Duration Curve \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
        ax.set_title('Flow Duration Curve \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    else: 
        #plt.title(f'{constituent} Exceedance Plot \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
        ax.set_title(f'{constituent} Exceedance Plot \n Station(s): ' + stations, **CFONT, fontsize = 12, weight = 'bold')
    # Add x label
    ax.set_xlabel('Exceedance Percentage', **CFONT, fontsize = 10)
    # Add y label
    ax.set_ylabel(f'{constituent} ({units})', **CFONT, fontsize = 10) 
    # Add legend
    ax.legend(handles=[obs, sim], fontsize = 9)
    # Set legend font to Calibri
    L = ax.legend()
    plt.setp(L.texts, family = 'Calibri')
    # Set the font and font size for the tick labels
    plt.xticks(**CFONT, fontsize = 9)
    plt.yticks(**CFONT, fontsize = 9)
    # Add axis gridlines
    ax.grid(which='major', axis='both', linewidth=0.3)
    ax.grid(which='minor', axis='y', linewidth=0.3)
    # Convert y axis to log scale
    ax.set_yscale('log')
    # Set the x axis minimum to 0
    ax.set_xlim(left=0)
    
    # Save figure, if given a folder or file path in argument save_path
    if save_path is not None:
        save_path = Path(save_path)
        if save_path.is_dir():
            filepath = save_path.joinpath(constituent + '_FDCexceedPoints_' + stations + '.png')
            fig.savefig(filepath, bbox_inches='tight')
        else:
            filepath = save_path
            fig.savefig(filepath, bbox_inches='tight')

    return fig, ax


def _exceedence(df):
        
    df['simulated rank'] = df.loc[:,'simulated'].rank(method = 'average', ascending = False)
    df['simulated exceed %'] =  df.loc[:,'simulated rank'] / (len(df) + 1) * 100
    df['observed rank'] =  df.loc[:,'observed'].rank(method = 'average', ascending = False)
    df['observed exceed %'] =  df.loc[:,'observed rank'] / (len(df) + 1) * 100

    return df