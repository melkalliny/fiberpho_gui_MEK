# %load_ext autoreload

# %autoreload 2
import io
import param
import panel as pn
import pandas as pd
import csv
import numpy as np
import os

import sys
import ipywidgets as ipw
import time
import plotly.express as px
import plotly.graph_objects as go
from scipy.optimize import curve_fit
from plotly.subplots import make_subplots
from pathlib import Path
import pickle
import logging
import traceback
from playsound import playsound
import FiberClass as fc


'''
Command to run script:
    Script : panel serve --show FiberGuiScript.py --websocket-max-message-size=104876000 --autoreload
    Notebook : panel serve FiberGuiNotebook.ipynb --websocket-max-message-size=104876000 --show
'''

#current obj version
current_version = 1
pn.extension('terminal', notifications = True, sizing_mode = 'stretch_width')
pn.extension('plotly')
#Dictionary of fiber objects
fiber_objs = {}
#Dataframe of object's info
fiber_data = pd.DataFrame(columns = ['Fiber #', 
                                     'Animal #', 
                                     'Exp. Date',
                                     'Exp. Start Time', 
                                     'Filename',
                                     'Behavior File'])

#Read fpho data
def run_init_fiberobj(event = None):
    # .value param to extract variables properly
    value = fpho_input.value
    file_name = fpho_input.filename
    obj_name = input_1.value
    if npm_format.value:
        fiber_num = input_2.value
    else:
        fiber_num = None
    animal_num = input_3.value_input
    exp_date = input_4.value_input
    exp_time = input_5.value_input
    start_time = input_6.value #looking for better name
    stop_time = input_7.value #looking for better name
    
     #Add input params to list for initialization
    input_params = []
    input_params.extend([obj_name, fiber_num, animal_num,
                         exp_date, exp_time, start_time, stop_time, file_name])
    if (input_params[0] in fiber_objs):
        pn.state.notifications.error(
            'Error: Please check logger for more info', duration = 4000)
        print('There is already an object with this name')
        return
        
    try:
        string_io = io.StringIO(value.decode("utf8"))
        df = pd.read_csv(string_io) #Read into dataframe
    except AttributeError:
        print("Make sure you choose a file")
        return
    except PermissionError:
        print("You do not have permission to access this file")
        return
          
    try:
        #Add to dict if object name does not already exist
        new_obj = fc.fiberObj(df, input_params[0], input_params[1],
                              input_params[2], input_params[3],
                              input_params[4], input_params[5], 
                              input_params[6], input_params[7])    
    except KeyError:
        logger.error(traceback.format_exc())
        pn.state.notifications.error(
            'Error: Please check logger for more information', duration = 4000)  
        print('It looks like theres something wrong with the format of your file')
        return
    except IndexError:
        logger.error(traceback.format_exc())
        pn.state.notifications.error(
            'Error: Please check logger for more information', duration = 4000)  
        print('Are you sure there are ', input_params[1], ' fibers in this file')
        return
    except Exception as e:
        logger.error(traceback.format_exc())
        pn.state.notifications.error(
            'Error: Please check logger for more information', duration = 4000)   
        return
            #Adds to dict
    fiber_objs[input_params[0]] = new_obj
    pn.state.notifications.success('Created ' + input_params[0] +
                                   ' object!', duration = 4000)
    #Adds to relevant info to dataframe
    fiber_data.loc[input_params[0]] = ([input_params[1], 
                                        input_params[2],
                                        input_params[3], 
                                        input_params[4],
                                        input_params[7],
                                        'NaN'])
    info_table.value = fiber_data
    existing_objs = fiber_objs
    #Updates selectors with new objects
    update_obj_selectas(existing_objs)
    last_filename = fpho_input.filename
    last_file = fpho_input.value
    
    return



# Upload pickled object files
def run_upload_fiberobj(event = None):
    upload = upload_pkl_selecta.filename
    try:
        for filename in upload:
            with io.open (filename, 'rb') as file:
                try:
                    temp = pickle.load(file)
                except EOFError:
                    pn.state.notifications.error(
                    'Error: Please check logger for more info',
                    duration = 4000)
                print("Error uploading " + filename +
                      ". Ensure this is a valid .pkl file")
                continue                    

            fiber_objs[temp.obj_name] = temp
            fiber_data.loc[temp.obj_name] = ([temp.fiber_num,
                                              temp.animal_num,
                                              temp.exp_date,
                                              temp.exp_start_time,
                                              temp.file_name,
                                              temp.beh_filename])
            info_table.value = fiber_data
            if not hasattr(temp_obj, 'version') and temp_obj != current_version:
                pn.state.notifications.error(
                'Warning: Please check logger for more info', duration = 4000)
                print("This pickle file is out of date." + 
                    "It may cause problems in certain functions")
        existing_objs = fiber_objs
        # Updates all cards with new objects
        update_obj_selectas(existing_objs)
        
        #Object uploaded notification
        pn.state.notifications.success('Uploaded ' + temp.obj_name
                                       + ' object!', duration = 4000)
        return
    except Exception as e:
        logger.error(traceback.format_exc())
        
# Combine two objects into one
def run_combine_objs(event = None):
    obj1 = fiber_objs[combine_obj_selecta1.value]
    obj2 = fiber_objs[combine_obj_selecta2.value]
    obj_name = combine_obj_name.value 
    combine_type = combine_type_selecta.value
    time_adj = combine_time.value
    new_obj = copy.deepcopy(obj1)
    
    if obj_name in fiber_objs:
        pn.state.notifications.error(
            'Error: Please check logger for more info', duration = 4000)
        print('There is already an object with this name')
        return
    
    try:
        #Add to dict if object name does not already exist
        new_obj.combine_objs(obj2, obj_name,
                             combine_type, time_adj)
                                 
    except KeyError:
        print('key error')
        return
    # except IndexError:
    #     logger.error(traceback.format_exc())
    #     return
    # except Exception as e: 
    #     return
            #Adds to dict
    fiber_objs[new_obj.obj_name] = new_obj
    pn.state.notifications.success('Created ' + new_obj.obj_name +
                                   ' object!', duration = 4000)
    #Adds to relevant info to dataframe
    fiber_data.loc[new_obj.obj_name] = ([new_obj.fiber_num, 
                                        new_obj.animal_num,
                                        new_obj.exp_date, 
                                        new_obj.exp_start_time,
                                        new_obj.file_name,
                                        new_obj.beh_filename])
    info_table.value = fiber_data
    existing_objs = fiber_objs
    #Updates selectors with new objects
    update_obj_selectas(existing_objs)
    return
        
# Deletes selected object
def run_delete_fiberobj(event = None):
    for obj in delete_obj_selecta.value:
        try:
            del fiber_objs[obj]
        except Exception as e:
            logger.error(traceback.format_exc())
            pn.state.notifications.error(
                'Error: Please check logger for more info', duration = 4000)
            print("Error: Cannot delete " + obj + ", please try again.")
            continue
        fiber_data.drop([obj], axis = 0, inplace = True)
    info_table.value = fiber_data
    existing_objs = fiber_objs
    # Updates all cards with new objects
    update_obj_selectas(existing_objs)
    return

# Saves selected object to pickle file
def run_save_fiberobj(event = None):
    for obj in save_obj_selecta.value:
        try:
            temp = fiber_objs[obj]
            with open(obj + '.pickle', 'wb') as handle:
                pickle.dump(temp, handle)
            pn.state.notifications.success('# ' + temp.obj_name
                                           + ' pickled successfully',
                                           duration = 4000)
            print(temp.obj_name + " saved")
        except Exception as e:
            pn.state.notifications.error(
                'Error: Please check logger for more info', duration = 4000)
            logger.error(traceback.format_exc())
            print("Error: Cannot save object, please try again.")
            continue
    return
        
        
# Creates raw plot pane
def run_plot_raw_trace(event):
    # .value param to extract variables properly
    selected_objs = obj_selecta.value
    #For len of selected objs, create and plot raw signal graph
    for objs in selected_objs:
        temp = fiber_objs[objs]
        #Creates pane for plotting
        plot_pane = pn.pane.Plotly(height = 300,
                                   sizing_mode = "stretch_width")
        #Sets figure to plot variable
        try:
            plot_pane.object = temp.raw_signal_trace() 
            plot_raw_card.append(plot_pane) #Add figure to template
            if save_pdf_rawplot.value:
                fig.write_image(temp.obj_name + "_raw_data.pdf")
        #playsound(correct_chime)
        except Exception as e:
            logger.error(traceback.format_exc())
            pn.state.notifications.error(
                'Error: Please check logger for more info', duration = 4000)
            continue
    return
        
        
# Creates normalize signal pane
def run_normalize_a_signal(event = None):
    # .value param to extract variables properly
    selected_objs = norm_selecta.value
    #For len of selected objs, create and plot raw signal graph
    for objs in selected_objs:
        temp = fiber_objs[objs]
        #Creates pane for plotting
        plot_pane = pn.pane.Plotly(height = 900,
                                   sizing_mode = "stretch_width") 
        #Sets figure to plot variable
        try:
            fig = temp.normalize_a_signal(pick_signal.value,
                                                   pick_reference.value)
            plot_pane.object = fig
            norm_sig_card.append(plot_pane) #Add figure to template
            if save_pdf_norm.value:
                fig.write_image(objs + '_' + pick_signal.value + "_normalized.pdf")

        except Exception as e:
            logger.error(traceback.format_exc())
            pn.state.notifications.error(
                'Error: Please check logger for more info', duration = 4000)
            continue  
    return
        
#Read behavior data
def run_import_behavior_data(event = None):
    selected_obj = behav_selecta.value
    obj = fiber_objs[selected_obj]
    try:
        behav = behav_input.value
        filename = behav_input.filename
        file = behav.decode("utf8")
        obj.import_behavior_data(file, filename, 'place_holder')
        fiber_data.loc[obj.obj_name, 'Behavior File'] = obj.beh_filename
        info_table.value = fiber_data
        pn.state.notifications.success('Uploaded Behavior data for '
                                       + obj.obj_name, duration = 4000)
    except FileNotFoundError:
            print("Could not find file: " + BORIS_filename)
            pn.state.notifications.error(
            'Error: Please check logger for more info', duration = 4000)
    except PermissionError:
            print("Could not access file: " + BORIS_filename)
            pn.state.notifications.error(
            'Error: Please check logger for more info', duration = 4000)
    except Exception as e:
        logger.error(traceback.format_exc())
        pn.state.notifications.error(
            'Error: Please check logger for more info', duration = 4000)
        return
    return
                
#Plot behavior on a full trace
def run_plot_behavior(event = None): 
    selected_objs = plot_beh_selecta.value
    #For len of selected objs, create and plot behavior data
    for objs in selected_objs:
        temp = fiber_objs[objs]
        # if temp.beh_file is None: # Bug: Plot behavior still runs even without behavior file
        #Creates pane for plotting
        plot_pane = pn.pane.Plotly(height = 500,
                                   sizing_mode = "stretch_width") 
        #Sets figure to plot variable
        try:
            plot_pane.object = temp.plot_behavior(behavior_selecta.value,
                                              channel_selecta.value) 
            plot_beh_card.append(plot_pane) #Add figure to template
            if save_pdf_beh.value:
                fig.write_image(objs + "_behavior_plot.pdf")
        except Exception as e:
            logger.error(traceback.format_exc())
            pn.state.notifications.error(
                'Error: Please check logger for more info', duration = 4000)
            continue
    return

             
#Plot zscore of a point evnt
def run_plot_zscore(event = None): 
    selected_objs = zscore_selecta.value
    baseline_vals = np.array([baseline_start.value, baseline_end.value])
    # How user would like to apply the baseline window input
    baseline_option = baseline_selecta.value
        #For len of selected objs, create and plot zscores
    for objs in selected_objs:
        temp = fiber_objs[objs]
        for beh in zbehs_selecta.value:
            for channel in zchannel_selecta.value:
                #Creates pane for plotting
                plot_pane = pn.pane.Plotly(height = 500,
                                           sizing_mode = "stretch_width") 
                #Sets figure to plot variable
                try:
                    plot_pane.object = temp.plot_zscore(channel, beh, 
                                                        time_before.value, 
                                                        time_after.value, 
                                                        baseline_vals, 
                                                        baseline_option,
                                                        first_trace.value,
                                                        last_trace.value,
                                                        show_every.value,
                                                        save_csv.value,
                                                        percent_bool.value) 
                    zscore_card.append(plot_pane) #Add figure to template

                    if save_pdf_PSTH.value:
                        fig.write_image(objs + "_PSTH.pdf")
                except Exception as e:
                    logger.error(traceback.format_exc())
                    pn.state.notifications.error(
                        'Error: Please check logger for more info', duration = 4000)
                    continue

    return
                
# Runs the pearsons correlation coefficient
def run_pearsons_correlation(event = None):
    try:
        name1 = pearsons_selecta1.value
        name2 = pearsons_selecta2.value
        obj1 = fiber_objs[name1]
        obj2 = fiber_objs[name2]
        channel1 = channel1_selecta.value
        channel2 = channel2_selecta.value
        start = pears_start_time.value
        end = pears_end_time.value
        #Creates pane for plot
        plot_pane = pn.pane.Plotly(height = 300,
                                   sizing_mode = "stretch_width") 
        plot_pane.object = obj1.pearsons_correlation(obj2,
                                                     channel1, channel2,
                                                     start, end)
        pearsons_card.append(plot_pane) #Add figure to template
        if save_pdf_time_corr.value:
            fig.write_image(name1 + '_' + name2 + "_correlation.pdf")
    except ValueError:
        return
    except Exception as e:
        logger.error(traceback.format_exc())
        pn.state.notifications.error(
            'Error: Please check logger for more info', duration = 4000)
        return
    return

def run_beh_specific_pearsons(event = None):
    for channel in beh_corr_channel_selecta.value:
        for behavior in beh_corr_behavior_selecta.value:
            name1 = beh_corr_selecta1.value
            name2 = beh_corr_selecta2.value
            obj1 = fiber_objs[name1]
            obj2 = fiber_objs[name2]
            channel1 = beh_corr_channel_selecta1.value
            channel2 = beh_corr_channel_selecta2.value
            #Creates pane for plot
            plot_pane = pn.pane.Plotly(height = 300,
                                       sizing_mode = "stretch_width")
            try:
                plot_pane.object = obj1.behavior_specific_pearsons(obj2,
                                                                   channel1,
                                                                   channel2, 
                                                                   behavior)
                beh_corr_card.append(plot_pane) #Add figure to template 
                if save_pdf_beh_corr.value:
                    fig.write_image(name1 + '_' + name2 + '_' + behavior + "_correlation.pdf")
            except Exception as e:
                logger.error(traceback.format_exc())
                pn.state.notifications.error(
                    'Error: Please check logger for more info', duration = 4000)
                continue 
    return
        

#Updates available signal options based on selected object
def update_selecta_options(event = None): 
    # Normalize Card
    selected_norm = norm_selecta.value
    if selected_norm:
        #For len of selected objs, create and plot behavior data
        available_channels = fiber_objs[selected_norm[0]].channels
        for objs in selected_norm:
            temp = fiber_objs[objs]
            available_channels = temp.channels & available_channels
        pick_signal.options = list(available_channels)
        pick_reference.options = list(available_channels) + [None]
    
    # Plot Behav card
    selected_behav = plot_beh_selecta.value
    if selected_behav:
        #For len of selected objs, create and plot behavior data
        available_channels = fiber_objs[selected_behav[0]].channels
        available_behaviors = fiber_objs[selected_behav[0]].behaviors
        for objs in selected_behav:
            temp = fiber_objs[objs]
            available_channels = temp.channels & available_channels
            available_behaviors = temp.behaviors & available_behaviors
        channel_selecta.options = list(available_channels)
        behavior_selecta.options = list(available_behaviors)
    
    # Z-Score card
    selected_zscore = zscore_selecta.value
    if selected_zscore:
        #For len of selected objs, create and plot zscores
        available_behaviors = fiber_objs[selected_zscore[0]].behaviors
        available_channels = fiber_objs[selected_zscore[0]].channels
        for objs in selected_zscore:
            temp = fiber_objs[objs]
            available_behaviors = temp.behaviors & available_behaviors
            available_channels = temp.channels & available_channels
        zbehs_selecta.options = list(available_behaviors)
        zchannel_selecta.options = list(available_channels)
      
    #Pearsons card
    name1 = pearsons_selecta1.value
    name2 = pearsons_selecta2.value
    obj1 = fiber_objs[name1]
    obj2 = fiber_objs[name2]
    available_channels1 = obj1.channels
    available_channels2 = obj2.channels
    channel1_selecta.options = list(available_channels1)
    channel2_selecta.options = list(available_channels2)
    
    #Correlation for a behavior
    name1 = beh_corr_selecta1.value
    name2 = beh_corr_selecta2.value
    obj1 = fiber_objs[name1]
    obj2 = fiber_objs[name2]
    available_channels1 = obj1.channels
    available_channels2 = obj2.channels
    available_behaviors = obj1.behaviors & obj2.behaviors
    beh_corr_channel_selecta1.options = list(available_channels1)
    beh_corr_channel_selecta2.options = list(available_channels2)
    beh_corr_behavior_selecta.options = list(available_behaviors)

    return
    
# Clear plots by card function
def clear_plots(event):
    if clear_raw.clicks:
        for i in range(len(plot_raw_card.objects)):
            if isinstance(plot_raw_card.objects[i], pn.pane.plotly.Plotly):
                plot_raw_card.remove(plot_raw_card.objects[i])
                return
    
    if clear_norm.clicks:
        for i in range(len(norm_sig_card.objects)):
            if isinstance(norm_sig_card.objects[i], pn.pane.plotly.Plotly):
                norm_sig_card.remove(norm_sig_card.objects[i])
                return
    
    if clear_beh.clicks:
        for i in range(len(plot_beh_card.objects)):
            if isinstance(plot_beh_card.objects[i], pn.pane.plotly.Plotly):
                plot_beh_card.remove(plot_beh_card.objects[i])
                return
    
    if clear_zscore.clicks:
        for i in range(len(zscore_card.objects)):
            if isinstance(zscore_card.objects[i], pn.pane.plotly.Plotly):
                zscore_card.remove(zscore_card.objects[i])
                return
    
    if clear_pears.clicks:
        for i in range(len(pearsons_card.objects)):
            if isinstance(pearsons_card.objects[i], pn.pane.plotly.Plotly):
                pearsons_card.remove(pearsons_card.objects[i])
                return
    
    if clear_beh_corr.clicks:
        for i in range(len(beh_corr_card.objects)):
            if isinstance(beh_corr_card.objects[i], pn.pane.plotly.Plotly):
                beh_corr_card.remove(beh_corr_card.objects[i])
                return
    
    return
            
# Convert lickometer data to boris csv
def run_convert_lick(event):
    file = lick_input.value
    name = lick_input.filename
    if file:
        try:
            string_io = io.StringIO(file.decode("utf8"))
            #Read into dataframe
            lick_file = pd.read_csv(string_io, delimiter = '\s+',
                                    names = ['Time', 'Licks']) 
        except FileNotFoundError:
            print("Could not find file: " + lick_input.filename)
            return
        except PermissionError:
            print("Could not access file: " + lick_input.filename)
            return
    if not lick_file.empty:
        try:
            convert = fc.lick_to_boris(lick_file)
            outputname = lick_input.filename[0:-4] + '_reformatted' + '.csv'
            sio = io.StringIO()
            convert.to_csv(sio, index = False)
            sio.seek(0)
            out_file = pn.widgets.FileDownload(sio, embed = True,
                                               filename = outputname,
                                               button_type = 'success',
                                               label = 'Download Formatted Lickometer Data',
                                               width = 400,
                                               sizing_mode = 'fixed')
            beh_tabs[1].append(out_file)
        except Exception as e:
            logger.error(traceback.format_exc())
            pn.state.notifications.error(
                'Error: Please check logger for more info', duration = 4000)
    else:
        print('Error reading file')
    return        

# Convert lickometer data to boris csv
def run_download_results(event):
    for types in result_type_selecta.value:
        results = pd.DataFrame()
        try:
            if types == 'Zscore Results':
                results = pd.concat([fiber_objs[name].z_score_results
                                    for name in results_selecta.value],
                                    ignore_index=True)
                results.to_csv(output_name.value + '_zscore_results.csv')
                pn.state.notifications.success(output_name.value +
                                            'Z-Score results downloaded',
                                            duration = 4000)
                print('Z-Score results saved locally to: ' +
                    output_name.value + '_zscore_results.csv')
            if types == 'Correlation Results':
                results = pd.concat([fiber_objs[name].correlation_results
                                    for name in results_selecta.value],
                                    ignore_index=True)
                results.to_csv(output_name.value + '_correlation_results.csv')
                pn.state.notifications.success(output_name.value +
                                            'Correlation results downloaded',
                                            duration = 4000)
                print('Correlation results saved locally to: ' +
                    output_name.value + '_correlation_results.csv')
            if types == 'Behavior Specific Correlation Reuslts':
                results = pd.concat([fiber_objs[name].beh_corr_results
                                    for name in results_selecta.value],
                                    ignore_index=True)
                results.to_csv(output_name.value +
                            '_behavior_correlation_results.csv')
                pn.state.notifications.success(output_name.value +
                                            'Behavior Correlation results downloaded',
                                            duration = 4000)
                print('Behavior Correlation results saved locally to: ' + 
                    output_name.value + '_behavior_correlation_results.csv')
        except Exception as e:
            logger.error(traceback.format_exc())
            pn.state.notifications.error(
                'Error: Please check logger for more info', duration = 4000)
            continue
    return

def update_obj_selectas(existing_objs):
    #Updates selectors with new objects
    obj_selecta.options = [*existing_objs]
    norm_selecta.options = [*existing_objs]
    behav_selecta.options = [*existing_objs]
    plot_beh_selecta.options = [*existing_objs]
    zscore_selecta.options = [*existing_objs]
    pearsons_selecta1.options = [*existing_objs]
    pearsons_selecta2.options = [*existing_objs]
    beh_corr_selecta1.options = [*existing_objs]
    beh_corr_selecta2.options = [*existing_objs]
    save_obj_selecta.options = [*existing_objs]
    combine_obj_selecta1.options = [*existing_objs]
    combine_obj_selecta2.options = [*existing_objs]
    delete_obj_selecta.options = [*existing_objs]
    results_selecta.options = [*existing_objs]
    return


# ----------------------------------------------------- # 
# Error logger
terminal = pn.widgets.Terminal(
    options = {"cursorBlink": False}, 
    height = 200,
    sizing_mode = 'stretch_width')
sys.stdout = terminal
# Logger settings
logger = logging.getLogger("terminal")
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler(terminal) # NOTE THIS
stream_handler.terminator = "  \n"
formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")

stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

#Buttons
clear_logs = pn.widgets.Button(name = 'Clear Logs', button_type = 'danger', 
                               height = 30, width = 40,
                               sizing_mode = 'fixed', align = 'end')

clear_logs.on_click(terminal.clear)

logger_info = pn.pane.Markdown(""" ##Logger
                            """, height = 40, width = 60)

log_card = pn.Card(pn.Row(logger_info, clear_logs), terminal, title = 'Logs', 
                   background = 'WhiteSmoke', width = 600,
                   collapsed = False, collapsible = False)

# ----------------------------------------------------- # 
# Init fiberobj Widget

#Input variables
fpho_input = pn.widgets.FileInput(name = 'Upload FiberPho Data',
                                  accept = '.csv') #File input parameter
npm_format = pn.widgets.Checkbox(name='Npm format', value = True, align = 'center')
input_1 = pn.widgets.TextInput(name = 'Object Name', width = 90, value = 'Obj1')
input_2 = pn.widgets.IntInput(name = 'Fiber Number', start = 1, end = 16, 
                              width = 80, placeholder = 'Int')
input_3 = pn.widgets.TextInput(name = 'Animal Number',  
                              width = 80, placeholder = 'String')
input_4 = pn.widgets.TextInput(name = 'Exp Date', width = 90, placeholder = 'Date')
input_5 = pn.widgets.TextInput(name = 'Exp Time', width = 90, placeholder = 'Time')
input_6 = pn.widgets.IntInput(name = 'Exclude time from beginning of recording',
                               width = 90, placeholder = 'Seconds', value = 0) #looking for better name
input_7 = pn.widgets.IntInput(name = 'Stop time from the beginning',
                               width = 90, placeholder = 'Seconds',
                              value = -1) #looking for better name
fiber_num_row = pn.Row(input_2, npm_format)

input_col = pn.Column(input_3, input_4,
                      input_5, input_6, input_7)
#Buttons
upload_button = pn.widgets.Button(name = 'Create Object',
                                  button_type = 'primary',
                                  width = 500, sizing_mode = 'stretch_width',
                                  align = 'end')
upload_button.on_click(run_init_fiberobj) #Button action

#Box
init_obj_box = pn.WidgetBox('# Create new fiber object', fpho_input,
                            input_1, fiber_num_row,
                            '**Experiment Info**', input_col,
                            '**Crop your data**', input_6, 
                            input_7, upload_button)

# ----------------------------------------------------- # 
# ----------------------------------------------------- # 
#Load fiberobj Widget

#Input variables
#File input parameter
upload_pkl_selecta = pn.widgets.FileInput(name = 'Upload Saved Fiber Objects',
                                          accept = '.pickle', multiple = True) 

#Buttons
upload_pkl_btn = pn.widgets.Button(name = 'Upload Object(s)', 
                                   button_type = 'primary', 
                                   width = 500, sizing_mode = 'stretch_width',
                                   align = 'end')
upload_pkl_btn.on_click(run_upload_fiberobj) #Button action

#Box
load_obj_box = pn.WidgetBox('# Reload saved Fiber Objects',
                            upload_pkl_selecta, upload_pkl_btn)

# ----------------------------------------------------- #
# ----------------------------------------------------- # 
#Combine fiberobjs Widget

#Input variables
#File input parameter
combine_obj_name = pn.widgets.TextInput(name = 'New Object Name', value = '',
                                       width = 80)
combine_obj_selecta1 = pn.widgets.Select(name = 'First Object', value = [],
                                         options = [])
combine_obj_selecta2 = pn.widgets.Select(name = 'First Object', value = [],
                                         options = [])
combine_type_selecta = pn.widgets.Select(name = 'Stitch type',
                                         value = 'Obj2 starts immediately after Obj1',
                                         options = ['Use Obj2 current start time',
                                                  'Use x secs for Obj2s start time',
                                                  'Obj2 starts immediately after Obj1',
                                                  'Obj2 starts x secs after Obj1 ends'])

combine_time = pn.widgets.TextInput(name = 'x secs', value = '0',
                                       width = 80)


#Buttons
combine_obj_btn = pn.widgets.Button(name = 'Combine Objects',
                                   button_type = 'primary',
                                   width = 500, sizing_mode = 'stretch_width',
                                   align = 'end')
combine_obj_btn.on_click(run_combine_objs) #Button action

#Box
combine_obj_box = pn.WidgetBox('# Combine two existing fiber objs',
                               combine_obj_name, combine_obj_selecta1,
                               combine_obj_selecta2, combine_type_selecta,
                               combine_time, combine_obj_btn)

# ----------------------------------------------------- # 
# ----------------------------------------------------- # 
#Delete fiberobj Widget

#Input variables
delete_obj_selecta = pn.widgets.MultiSelect(name = 'Fiber Objects',
                                          value = [], options = [])

#Buttons
delete_obj_btn = pn.widgets.Button(name = 'Delete Object',
                                   button_type = 'danger', width = 500,
                                   sizing_mode = 'stretch_width', 
                                   align = 'end')
delete_obj_btn.on_click(run_delete_fiberobj) #Button action

#Box
delete_obj_box = pn.WidgetBox('# Delete unwanted Fiber Objects', 
                              delete_obj_selecta, delete_obj_btn)

# ----------------------------------------------------- #

# ----------------------------------------------------- # 
#Save fiberobj Widget

#Input variables
save_obj_selecta = pn.widgets.MultiSelect(name = 'Fiber Objects',
                                          value = [], options = [], )

#Buttons
save_obj_btn = pn.widgets.Button(name = 'Save Object',
                                 button_type = 'primary', width = 400,
                                 sizing_mode = 'stretch_width',
                                 align = 'end')
save_obj_btn.on_click(run_save_fiberobj) #Button action

#Box
save_obj_box = pn.WidgetBox('# Save Fiber Objects for later',
                            save_obj_selecta, save_obj_btn)

# ----------------------------------------------------- #

# ----------------------------------------------------- # 
#Plot raw signal Widget

#Input variables
obj_selecta = pn.widgets.MultiSelect(name = 'Fiber Objects', value = [],
                                     options = [], )

#Buttons
plot_raw_btn = pn.widgets.Button(name = 'Plot Raw Signal',
                                 button_type = 'primary',
                                 width = 200,
                                 sizing_mode = 'stretch_width',
                                 align = 'start')
plot_raw_btn.on_click(run_plot_raw_trace)
clear_raw = pn.widgets.Button(name = 'Clear Plots \u274c',
                              button_type = 'danger', width = 30, 
                              sizing_mode = 'fixed', align = 'start')
clear_raw.on_click(clear_plots)

raw_info = pn.pane.Markdown("""
                                - Plots the raw signal outputs of fiber objects.
                            """, width = 200)

save_pdf_rawplot = pn.widgets.Checkbox(name = 'Save plot as pdf', value = False)

#Box
plot_options = pn.Column(obj_selecta, plot_raw_btn)
plot_raw_widget = pn.WidgetBox(raw_info, plot_options)
raw_plot_ops = pn.Row(save_pdf_rawplot, clear_raw,
                  sizing_mode = 'stretch_width',
                  margin = (0, 100, 0, 0))
plot_raw_card = pn.Card(plot_raw_widget, raw_plot_ops,
                        title = 'Plot Raw Signal',
                        background = 'WhiteSmoke',
                        width = 600, collapsed = True)

# ----------------------------------------------------- # 
#Normalize signal to reference Widget
#Input vairables

norm_selecta = pn.widgets.MultiSelect(name = 'Fiber Objects', value = [],
                                      options = [], )
pick_signal = pn.widgets.Select(name = 'Signal', options = [])
pick_reference = pn.widgets.Select(name = 'Reference', options = [])

#Buttons
norm_sig_btn = pn.widgets.Button(name = 'Normalize Signal',
                                 button_type = 'primary', width = 200,
                                 sizing_mode = 'stretch_width',
                                 align = 'start')
norm_sig_btn.on_click(run_normalize_a_signal)
update_norm_options_btn = pn.widgets.Button(name = 'Update Options',
                                            button_type = 'primary', 
                                            width = 200,
                                            sizing_mode = 'stretch_width',
                                            align = 'start')
update_norm_options_btn.on_click(update_selecta_options)
clear_norm = pn.widgets.Button(name = 'Clear Plots \u274c',
                               button_type = 'danger', width = 30,
                               sizing_mode = 'fixed', align = 'start')
clear_norm.on_click(clear_plots)

norm_info = pn.pane.Markdown("""
                                    - Normalizes the signal and reference trace 
                                    to a biexponential, linearly fits the normalized 
                                    reference to the normalized signal. <br>
                                    Stores all fitted traces in the dataframe and 
                                    plots them for examination.""",
                             width = 200)
save_pdf_norm = pn.widgets.Checkbox(name = "Save plot as pdf", value = False)
#Box
norm_options = pn.Column(norm_selecta, update_norm_options_btn, pick_signal,
                         pick_reference, norm_sig_btn)
norm_sig_widget = pn.WidgetBox('# Normalize Signal', norm_info, norm_options)
norm_plot_ops = pn.Row(save_pdf_norm, clear_norm,
                        sizing_mode = 'stretch_width',
                        margin = (0, 100, 0, 0))
norm_sig_card = pn.Card(norm_sig_widget, norm_plot_ops,
                        title = 'Normalize to a reference',
                        background = 'WhiteSmoke',
                        width = 600, collapsed = True)


# ----------------------------------------------------- # 
#Add Behavior Widget

#Input variables
behav_input = pn.widgets.FileInput(name = 'Upload Behavior Data',
                                   accept = '.csv') #File input parameter
behav_selecta = pn.widgets.Select(name = 'Fiber Objects', value = [],
                                  options = [], )
lick_input = pn.widgets.FileInput(name = 'Upload Lickometer Data',
                                  accept = '.csv')

#Buttons
upload_beh_btn = pn.widgets.Button(name = 'Read Behavior Data',
                                   button_type = 'primary', width = 200,
                                   sizing_mode = 'stretch_width',
                                   align = 'start')
upload_beh_btn.on_click(run_import_behavior_data) #Button action
upload_lick_btn = pn.widgets.Button(name = 'Upload', button_type = 'primary',
                                    width = 100, sizing_mode = 'fixed')
upload_lick_btn.on_click(run_convert_lick)

upload_beh_info = pn.pane.Markdown("""
                                        - Imports user uploaded behavior data and reads
                                        dataframe to update and include subject, behavior,
                                        and status columns to the dataframe.
                                    """, width = 200)

convert_info = pn.pane.Markdown(""" - Upload lickometer data to be converted 
                                to behavior file formatting <br> - Returns downloadable
                                csv after conversion has been completed""",
                                width = 200)


#Box
behav_options = pn.Column(upload_beh_info, behav_selecta,
                          behav_input, upload_beh_btn)
lick_options = pn.Column(convert_info, lick_input, upload_lick_btn)
beh_tabs = pn.Tabs(('Behavior Import', behav_options),
                   ('Lick 2 Boris', lick_options))

upload_beh_widget = pn.WidgetBox(beh_tabs, height = 270)
upload_beh_card = pn.Card(upload_beh_widget, title = 'Import Behavior', 
                          background = 'WhiteSmoke', collapsed = False)


# ----------------------------------------------------- # 

# ----------------------------------------------------- # 
#Add Behavior plot Widget

#Input variables
plot_beh_selecta = pn.widgets.MultiSelect(name = 'Fiber Objects', value = [],
                                          options = [], )
channel_selecta = pn.widgets.MultiSelect(name = 'Signal', value = [],
                                         options = [], )
behavior_selecta = pn.widgets.MultiSelect(name = 'Behavior', value = [],
                                          options = [], )

#Buttons
plot_beh_btn = pn.widgets.Button(name = 'Plot Behavior',
                                 button_type = 'primary', width = 200,
                                 sizing_mode = 'stretch_width',
                                 align = 'start')
plot_beh_btn.on_click(run_plot_behavior) #Button action
update_plot_options_btn = pn.widgets.Button(name = 'Update Options',
                                            button_type = 'primary',
                                            width = 200,
                                            sizing_mode = 'stretch_width',
                                            align = 'start')
update_plot_options_btn.on_click(update_selecta_options) #Button action
clear_beh = pn.widgets.Button(name = 'Clear Plots \u274c',
                              button_type = 'danger',
                              width = 30, sizing_mode = 'fixed',
                              align = 'start')
clear_beh.on_click(clear_plots)

beh_info = pn.pane.Markdown("""
                                - Creates and displays the different channels from behavior data. <br>
                            """, width = 200)
save_pdf_beh = pn.widgets.Checkbox(name = 'Save plot as pdf', value = False)
#Box
plot_beh_options = pn.Column(plot_beh_selecta, update_plot_options_btn,
                             channel_selecta, behavior_selecta, plot_beh_btn)
plot_beh_widget = pn.WidgetBox(beh_info, plot_beh_options)
beh_plot_ops = pn.Row(save_pdf_beh, clear_beh, 
                      sizing_mode = 'stretch_width',
                      margin = (0, 100, 0, 0))
plot_beh_card = pn.Card(plot_beh_widget, beh_plot_ops,
                        title = 'Plot Behavior', background = 'WhiteSmoke',
                        width = 600, collapsed = True)

# ----------------------------------------------------- # 
# ----------------------------------------------------- # 
#Plot Z-Score

#Input variables
save_csv = pn.widgets.Checkbox(name = 'Save CSV')
percent_bool = pn.widgets.Checkbox(name = "Use % of baseline instead of Z-score")
zscore_selecta = pn.widgets.MultiSelect(name = 'Fiber Objects', value = [],
                                        options = [], )
zbehs_selecta = pn.widgets.MultiSelect(name = 'Behavior', value = [],
                                       options = [], )
zchannel_selecta = pn.widgets.MultiSelect(name = 'Signal', value = [],
                                          options = [], )
time_before = pn.widgets.IntInput(name = 'Time before event(s)',  width = 50,
                                  placeholder = 'Seconds', value = 2)
time_after = pn.widgets.IntInput(name = 'Time after initiation(s)',
                                 width = 50, placeholder = 'Seconds',
                                 value = 5)
baseline_start = pn.widgets.IntInput(name = 'Baseline Start Time (s)', 
                                     width = 50, placeholder = 'Seconds',
                                     value = 0)
baseline_end = pn.widgets.IntInput(name = 'Baseline End Time (s)', 
                                   width = 50, placeholder = 'Seconds',
                                   value = 0)
first_trace = pn.widgets.IntInput(name = 'Show traces from event number __', 
                                  width = 50, placeholder = "start",
                                  value = -1)
last_trace = pn.widgets.IntInput(name = 'to event number __', 
                                 width = 50, placeholder = "end", value = 0)
show_every = pn.widgets.IntInput(name = 'Show one in every __ traces', 
                                 width = 50, placeholder = "1", value = 1)

z_score_note = pn.pane.Markdown("""
                                   ***Note :***<br>
                                   - Baseline Window Parameters should be kept 0 unless you are using baseline<br> 
                                   z-score computation method. <br>
                                   - The parameters are in seconds. <br>
                                   - Please check where you would like your baseline window <br>
                                   - **ONLY CHECK ONE BOX** <br>
                                   """, width = 200)
zscore_info = pn.pane.Markdown("""
                                    - Takes a dataframe and creates a plot of z-scores for
                                    each time a select behavior occurs with the average
                                    z-score and SEM.
                                """, width = 200)

save_pdf_PSTH = pn.widgets.Checkbox(name = "Save plot as pdf", value = False)

#Buttons
zscore_btn = pn.widgets.Button(name = 'Zscore of Behavior', 
                               button_type = 'primary', width = 200,
                               sizing_mode = 'stretch_width',
                               align = 'start')
zscore_btn.on_click(run_plot_zscore) #Button action
options_btn = pn.widgets.Button(name = 'Update Options',
                                button_type = 'primary', width = 200,
                                sizing_mode = 'stretch_width',
                                align = 'start')
options_btn.on_click(update_selecta_options) #Button action

baseline_selecta = pn.widgets.RadioBoxGroup(name = 'Baseline Options',
                                            value = 'Each event',
                                            options = ['Each event',
                                                        'Start of Sample',
                                                       'Before Events',
                                                       'End of Sample'], 
                                            inline = True)
clear_zscore = pn.widgets.Button(name = 'Clear Plots \u274c',
                                 button_type = 'danger', width = 30,
                                 sizing_mode = 'fixed', align = 'start')
clear_zscore.on_click(clear_plots)

#Box
zscore_options = pn.Column(zscore_selecta, options_btn, zchannel_selecta, 
                           zbehs_selecta, time_before, time_after)
baseline_options = pn.Column(z_score_note, baseline_start,
                             baseline_end, baseline_selecta)
trace_options = pn.Column(first_trace, last_trace, show_every)
check_boxes = pn.Row(save_csv, percent_bool)
tabs = pn.Tabs(('Z-Score', zscore_options),
               ('Baseline Options', baseline_options), 
               ('Reduce Displayed Traces', trace_options))
zscore_widget = pn.WidgetBox('# Zscore Plot', zscore_info, tabs, zscore_btn, check_boxes)
zscore_plot_ops = pn.Row(save_pdf_PSTH, clear_zscore, 
                         sizing_mode = 'stretch_width', 
                         margin = (0, 100, 0, 0))
zscore_card = pn.Card(zscore_widget, zscore_plot_ops,
                      title = 'Zscore Plot', background = 'WhiteSmoke',
                      width = 600, collapsed = True)

# ----------------------------------------------------- # 
# ----------------------------------------------------- # 
#Pearsons Correlation widget

#Input variables
pearsons_selecta1 = pn.widgets.Select(name = 'Object 1', value = [],
                                      options = [], )
pearsons_selecta2 = pn.widgets.Select(name = 'Object 2', value = [],
                                      options = [], )
channel1_selecta = pn.widgets.Select(name = 'Signal', value = [],
                                     options = [])
channel2_selecta = pn.widgets.Select(name = 'Signal', value = [],
                                     options = [])
pears_start_time = pn.widgets.IntInput(name = 'Start Time', width = 50, 
                                       placeholder = 'Seconds', value = 0)
pears_end_time = pn.widgets.IntInput(name = 'End Time', width = 50,
                                     placeholder = 'Seconds', value = -1)

save_pdf_time_corr = pn.widgets.Checkbox(name = 'Save plot as pdf', value = False)

#Buttons
pearsons_btn = pn.widgets.Button(name = 'Calculate Pearsons Correlation',
                                 button_type = 'primary', width = 200,
                                 sizing_mode = 'stretch_width',
                                 align = 'start')
pearsons_btn.on_click(run_pearsons_correlation) #Button action
pearson_options_btn = pn.widgets.Button(name = 'Update Options',
                                        button_type = 'primary', width = 200,
                                        sizing_mode = 'stretch_width',
                                        align = 'start')
pearson_options_btn.on_click(update_selecta_options) #Button action
clear_pears = pn.widgets.Button(name = 'Clear Plots \u274c',
                                button_type = 'danger', width = 30,
                                sizing_mode = 'fixed', align = 'start')
clear_pears.on_click(clear_plots)

pears_info = pn.pane.Markdown("""
                                    - Takes in user chosen objects and channels 
                                    then returns the Pearson's correlation coefficient 
                                    and plots the signals.
                                """, 
                                width = 200)

#Box
pearson_row1  = pn.Row(pearsons_selecta1, pearsons_selecta2)
pearson_row2  = pn.Row(channel1_selecta, channel2_selecta)
pearson_row3  = pn.Row(pears_start_time, pears_end_time)
pearson_widget = pn.WidgetBox('# Pearons Correlation Plot', pears_info,
                              pearson_row1, pearson_options_btn, pearson_row2,
                              pearson_row3, pearsons_btn)
pearsons_plot_ops = pn.Row(save_pdf_time_corr, clear_pears,
                            sizing_mode = 'stretch_width',
                            margin = (0, 100, 0, 0))
pearsons_card = pn.Card(pearson_widget, pearsons_plot_ops,
                        title = 'Pearsons Correlation Coefficient',
                        background = 'WhiteSmoke', width = 600,
                        collapsed = True)


# ----------------------------------------------------- # 
# ----------------------------------------------------- # 
#Behavior specific pearsons widget

#Input variables
beh_corr_selecta1 = pn.widgets.Select(name = 'Object 1', value = [],
                                      options = [], )
beh_corr_selecta2 = pn.widgets.Select(name = 'Object 2', value = [],
                                      options = [], )
beh_corr_channel_selecta1 = pn.widgets.Select(name = 'Signal', value = [],
                                                  options = [])
beh_corr_channel_selecta2 = pn.widgets.Select(name = 'Signal', value = [],
                                                  options = [])
beh_corr_behavior_selecta = pn.widgets.MultiSelect(name = 'Behavior',
                                                   value = [], options = [], )

#Buttons
beh_corr_btn = pn.widgets.Button(name = 'Calculate Pearsons Correlation',
                                 button_type = 'primary', width = 200,
                                 sizing_mode = 'stretch_width',
                                 align = 'start')
beh_corr_btn.on_click(run_beh_specific_pearsons) #Button action
beh_corr_options_btn = pn.widgets.Button(name = 'Update Options',
                                         button_type = 'primary', width = 200,
                                         sizing_mode = 'stretch_width',
                                         align = 'start')
beh_corr_options_btn.on_click(update_selecta_options) #Button action
clear_beh_corr = pn.widgets.Button(name = 'Clear Plots \u274c',
                                   button_type = 'danger', width = 30,
                                   sizing_mode = 'fixed', align = 'start')
clear_beh_corr.on_click(clear_plots)

beh_corr_info = pn.pane.Markdown("""
                                    - Takes in user chosen objects, channels 
                                    and behaviors to calculate the behavior specific Pearson’s 
                                    correlation and plot the signals. <br>
                                """, width = 200)

save_pdf_beh_corr = pn.widgets.Checkbox(name = 'Save plot as pdf', value = False)


#Box
obj_row  = pn.Row(beh_corr_selecta1, beh_corr_selecta2)
channel_row  = pn.Row(beh_corr_channel_selecta1, beh_corr_channel_selecta2)
beh_corr_options = pn.Column(obj_row, beh_corr_options_btn, channel_row,
                             beh_corr_behavior_selecta, beh_corr_btn)
beh_corr_widget = pn.WidgetBox('# Behavior Specific Correlation Plot', 
                                beh_corr_info, beh_corr_options)
beh_corr_plot_ops = pn.Row(save_pdf_beh_corr, clear_beh_corr,
                            sizing_mode = 'stretch_width', 
                            margin = (0, 100, 0, 0))
beh_corr_card = pn.Card(beh_corr_widget, beh_corr_plot_ops,
                        title = 'Behavior Specific Pearsons Correlation',
                        background = 'WhiteSmoke', width = 600,
                        collapsed = True)


# ----------------------------------------------------- # 
# ----------------------------------------------------- # 
#Download Results widget

#Input variables
output_name = pn.widgets.TextInput(name = 'Output filename', width = 90,
                                   placeholder = 'String')
results_selecta = pn.widgets.MultiSelect(name = 'Fiber Objects', value = [],
                                         options = [])
result_type_selecta= pn.widgets.MultiSelect(name = 'Result Types', value = [],
                                            options = ['Zscore Results',
                                                       'Correlation Results',
                                                       'Behavior Specific Correlation Reuslts'])

#Buttons
download_results_btn = pn.widgets.Button(name = 'Download',
                                 button_type = 'primary', width = 200,
                                 sizing_mode = 'stretch_width',
                                 align = 'start')

download_results_btn.on_click(run_download_results) #Button action

#Box
download_results_widget = pn.WidgetBox('# Download Results', output_name,
                                       results_selecta, result_type_selecta,
                                       download_results_btn)
download_results_card = pn.Card(download_results_widget,
                                title = 'Download Results',
                                background = 'WhiteSmoke', width = 600,
                                collapsed = True)

# ----------------------------------------------------- # 
# ----------------------------------------------------- # 
#Object info widget

#Table
info_table = pn.widgets.Tabulator(fiber_data, height = 270, 
                                  page_size = 10, disabled = True)

obj_info_card = pn.Card(info_table, title = "Display Object Attributes", 
                        background = 'WhiteSmoke', collapsed = False)

# ----------------------------------------------------- # 
# Template settings
# Accent Colors
ACCENT_COLOR_HEAD = "#D9F3F3"
ACCENT_COLOR_BG = "#128CB6"

# Material Template
material = pn.template.MaterialTemplate(
    site = 'Donaldson Lab: Fiber Photometry', 
    title = 'FiberPho GUI',
    header_color = ACCENT_COLOR_HEAD,
    header_background = ACCENT_COLOR_BG)


# Append widgets to Material Template
material.sidebar.append(pn.pane.Markdown(
    "** Upload your photometry data *(.csv)* ** and set your fiber object's **attributes** here"))
material.sidebar.append(init_obj_box)
material.sidebar.append(load_obj_box)
material.sidebar.append(combine_obj_box)
material.sidebar.append(save_obj_box)
material.sidebar.append(delete_obj_box)

material.main.append(pn.Row(upload_beh_card, obj_info_card))
material.main.append(plot_raw_card)
material.main.append(norm_sig_card)
material.main.append(plot_beh_card)
material.main.append(zscore_card)
material.main.append(pearsons_card)
material.main.append(beh_corr_card)
material.main.append(download_results_card)
material.main.append(log_card)

material.servable()