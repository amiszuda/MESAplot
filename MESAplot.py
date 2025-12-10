#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# MESA plotter, to plot MESA output easier
#
#    Author: Amadeusz Miszuda    / XI.2021 
#                                /  X.2023 - data column names now availlable using -n option, works under curses
#                                /XII.2023 - added twin y axis support, accesible via u 1:2:3
#                                /  I.2024 - added some cool stuff, like recursive search for history.data files, size-map or saving plots
#                                / XI.2024 - add/disable legend (default disabled)
#
#                                TO FIX:
#                                -r not working with -n
#                                -different marker sizes for additional columns, e.g. by using uc (u colormap 1:2) - done. FIX: legend values
#                                -color map 
#
#                                TO DO:
#                                -refresh the plot
#                                -multiuse - mu 1:2:3:4 to plot 1:2, 1:3, 1:4, so on... (???)
#
# Requirements: mesa-reader, history.data and/or profiles.data files 

import mesa_reader as mesa
import numpy as np
import glob
import sys
import os
os.environ['PYTHONWARNINGS'] = 'ignore'
import matplotlib.pyplot as plt
import curses

from matplotlib.ticker import FormatStrFormatter, AutoMinorLocator

try:
    # requires mactex on Mac,  
    # brew install --cask mactex 
    import scienceplots
    plt.style.use(['science', 'std-colors'])
    # plt.rcParams['text.latex.preamble'] = r'\usepackage{sfmath} \boldmath'
    # plt.rcParams('font', weight='bold')
except:
    pass

### Initialise rcParams ###
###########################
# from matplotlib import rcParams

# rcParams['axes.linewidth']   = 1.5
# rcParams['mathtext.fontset'] = 'stix'
# rcParams['font.family']      = 'STIXGeneral'
# rcParams["figure.autolayout"] = 'True'
# # rcParams['text.usetex'] = True

# rcParams['xtick.labelsize'] = 15
# rcParams['ytick.labelsize'] = 15
# rcParams['legend.fontsize'] = 13
# rcParams["axes.labelweight"] = "bold"



### Env variables ###
#####################
fontsize = 20 # size of the font used for the axis labels
labelsize = 15 # size of the font used for the tick labels
legend_fontsize = 10
title_fontsize = 15
sizemap_label_fontsize = 12
legend_linewidth = 2
markerscale = 0.9

label_prefix = ''#'MESA.'

include_legend = True

multiplicator = 1 # 86400



####### HELP ########
#####################
if len(sys.argv) < 3:
   print('\n    MESA-plotter  \n')
   print('      plot opt[u x:y] [lc[x,y]] \n')
   print('      lc               filename of your light curve containing at least 2 columns ')
   print('                       You can pass as many files to plot as you wish ')
   print('      <u x:y:z>        specify the column numbers to plot ')
   # print('       us              use size map -> plot the last column using size map ') # not working with -wl as default
   # print('      <mu x1:y1 x2:x2> (optional) specify multiple column numbers to plot <devel option!>')
   print('      -r               pass only the directory and look for any LOGS*/history.data files therein to plot ') 
   print('      -n               name module will print availlable data column names ')
   print('      -c               add cross hair cursor to the plot ')
   print('      -l / -/l         add / disable legend (disabled by default)')
   print('      -wl/wp/wlp       plot using lines [default], points, lines and points, respectively')
   print('      -xlog/ylog       adds log scale on a given axis')
   print('      -ylim            in multiple plot mode (plotting 3 variables) set y twin ax lim same as primary y ax lim')
   print('      -save=fname      save plot under the fname.extension. If no extension provided default to ".png" ')
   print('')
   exit()




### Initialise plot ###
#######################
fig, ax1 = plt.subplots(1, 1, figsize=(12,7))





# # load file list and pick up only those to plot
# file_list = []  
# for i in range(len(sys.argv)):
#     if os.path.exists(sys.argv[i]):
#         file_list.append(sys.argv[i])
# # delete posibble duplicates
# file_list = list(set(file_list))


# global numer_of_files
# numer_of_files = -1 # -1 to account for calling the program, which is sys.argv[0]
# for i in range(len(sys.argv)):
#     if os.path.exists(sys.argv[i]):
#            file_to_plot = sys.argv[i]
#            numer_of_files += 1


# Load file list and pick up only those to plot
file_list = []
to_remove = []  # Arg list to remove from sys.argv

for i in range(len(sys.argv)):
    if i == 0:
        # Discard the firts argument as being a path to program
        to_remove.append(sys.argv[i])
        continue

    if os.path.exists(sys.argv[i]):
        file_list.append(sys.argv[i])
        to_remove.append(sys.argv[i])  

# delete posibble duplicates
file_list = list(set(file_list))
file_list.sort()
# remove to_remove from sys.argv
sys.argv = [arg for arg in sys.argv if arg not in to_remove]

# Chech if '-r' i '-n' exist in sys.argv. Sort them if they do, so -n option will know that 
# it has to search recursively for LOGS*/*.data files!
if '-n' in sys.argv and '-r' in sys.argv:
    if sys.argv.index('-r') > sys.argv.index('-n'):
        r_index = sys.argv.index('-r')
        n_index = sys.argv.index('-n')
        sys.argv[r_index], sys.argv[n_index] = sys.argv[n_index], sys.argv[r_index]


##### Functions #####
#####################

def try_float(num):
    """
        Routine that checks if the passed via terminal command is float of not. 

        Parameters:
            num:     any type
        
        Returns:
            True/False
    """

    try:
        float(num)
        return True
    except ValueError:
        return False

# def onclick(event):
#     if event.button == 'r':
#         plt.draw() #redraw
#         plt.show()

def data_names(scr,search_for_history_file=False):
    """
        Routine that creates curses-based screen and prints the avaiable column names

        Parameters:
            current_ax:     matplotlib axes object
            other_ax:       matplotlib axes object
    """
    if search_for_history_file: search_for_hist(files)
    # Create curses screen
    scr.keypad(True)
    curses.use_default_colors()
    curses.noecho()
    scr.refresh()

    # Get screen width/height
    height,width = scr.getmaxyx()

    # Create a curses pad (pad size is height + 10)
    mypad_height = 32767

    mypad = curses.newpad(mypad_height, width);
    mypad.scrollok(True)
    mypad_pos = 0
    mypad_refresh = lambda: mypad.refresh(mypad_pos+2, 0, 2, 5, height-2, width-5)
    mypad_refresh()

    # Fill the window with text (note that 5 lines are lost forever)
    try:
        scr.addstr(0,0,'Availlable data column names in {} file '.format(file), curses.A_BOLD)
        scr.addstr(height-1,0, 'Press q to exit ', curses.A_REVERSE)

        for i in range(0, len(p.bulk_names)):
            # mypad.addstr(i,0,"{0} This is a sample string...\n".format(i))
            mypad.addstr(i,0,'{:3d} {}'.format(i+1, p.bulk_names[i]))

            if i > height: mypad_pos = min(i - height+3, mypad_height - height+3)
            mypad_refresh()
            #time.sleep(0.05)
        mypad_pos = -2  # Rewind the list to the beginning
        mypad_refresh()  # Refresh screen after adjusting scroll position

        # Wait for user to scroll or quit
        running = True
        while running:
            ch = scr.getch()
            if ch == curses.KEY_DOWN and mypad_pos < mypad.getyx()[0] - height + 2:
                mypad_pos += 2
                mypad_refresh()
            elif ch == curses.KEY_UP and mypad_pos > -2:
                mypad_pos -= 1
                mypad_refresh()
            elif ch < 256 and chr(ch) == 'q':
                running = False
            elif ch == curses.KEY_RESIZE:
                height,width = scr.getmaxyx()
                while mypad_pos > mypad.getyx()[0] - height + 1:
                  mypad_pos -= 1
                mypad_refresh()

    except KeyboardInterrupt: pass


    scr.keypad(0)
    curses.echo()
    curses.nocbreak()
    curses.endwin()

def make_format(current_ax, other_ax):
    """
        Display cursor value with two axes.

        Parameters:
            current_ax:     matplotlib axes object
            other_ax:       matplotlib axes object
    """

    # current_ax and other_ax are axes
    def format_coord(x, y):
        # x, y are data coordinates
        # convert to display coords
        display_coord = current_ax.transData.transform((x,y))
        inv = other_ax.transData.inverted()
        # convert back to data coords with respect to ax
        ax_coord = inv.transform(display_coord)
        coords = [ax_coord, (x, y)]
        return ('Left: {:<40}    Right: {:<}'
                .format(*['({:.3f}, {:.3f})'.format(x, y) for x,y in coords]))
    return format_coord

def set_ticks(ax=ax1, labelsize=labelsize):
    """
        Set ticks properties.

        Parameters:
            ax:             matplotlib axes object
                            specify which axes to characterize
            labelsize:      integer
                            set the tick font size
    """

    try:
        if ax == ax1: 
            ax.tick_params(which='minor', direction='in', bottom=True, top=True, left=True, right=True, length=2, width=1, labelsize=labelsize)
            ax.tick_params(direction='in', bottom=True, top=True, left=True, right=True, length=4, width=1, labelsize=labelsize)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            # in case of using scientific notation fix the tick label size (e.g., 1e10)
            ax.xaxis.get_offset_text().set_fontsize(labelsize)
            ax.yaxis.get_offset_text().set_fontsize(labelsize)
            ax.ticklabel_format(useMathText=True)
    except: pass
    try:
        # if ax1.twinx().axison: # check if axis is initialised 
        if ax == ax2: 
            ax.tick_params(direction='in', bottom=False, top=False, left=False, right=True, length=4, width=1, labelsize=labelsize)
            ax.tick_params(which='minor', direction='in', bottom=False, top=False, left=False, right=True, length=2, width=1, labelsize=labelsize)
            ax.format_coord = make_format(ax2, ax1) # display cursor value with two axes
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            # in case of using scientific notation fix the tick label size (e.g., 1e10)
            ax.yaxis.get_offset_text().set_fontsize(labelsize)
            ax.ticklabel_format(useMathText=True)
    except: pass

# def plot_columns(columns):
    # """
    #     Determine which columns to plot

    #     Parameters:
    #         columns:        
    # """
    # cols = columns
    # split_cols = str.rsplit(cols, sep=":") # split arg like '1:2' for two numbers

    # if len(split_cols) == 2:
    #     # if numbers of columns are provided
    #     if (try_float(split_cols[0]) is True):
    #         xcol = int(split_cols[0])
    #         ycol = int(split_cols[1])
    #         type = 'int'

    #         if xcol < 0: plt.gca().invert_xaxis()
    #         if ycol < 0: plt.gca().invert_yaxis()

    #     # if column names rather than column numbers are provided
    #     if (try_float(split_cols[0]) is False):
    #         xcol = split_cols[0]
    #         ycol = split_cols[1]
    #         type = 'str'

    #     use_columns = 2

    # if len(split_cols) == 3:
    #     # if numbers of columns are provided
    #     if (try_float(split_cols[0]) is True):
    #         xcol = int(split_cols[0])
    #         ycol = int(split_cols[1])
    #         zcol = int(split_cols[2])
    #         type = 'int'

    #         if xcol < 0: plt.gca().invert_xaxis()
    #         if ycol < 0: plt.gca().invert_yaxis()
    #         if zcol < 0: plt.gca().invert_yaxis()

    #     # if column names rather than column numbers are provided
    #     if (try_float(split_cols[0]) is False):
    #         xcol = split_cols[0]
    #         ycol = split_cols[1]
    #         zcol = split_cols[2]
    #         type = 'str'

    #     use_columns = 3

    # if len(split_cols) == 4:
    #     # if numbers of columns are provided
    #     if (try_float(split_cols[0]) is True):
    #         xcol = int(split_cols[0])
    #         ycol = int(split_cols[1])
    #         zcol = int(split_cols[2])
    #         ccol = int(split_cols[3])
    #         type = 'int'

    #         if xcol < 0: plt.gca().invert_xaxis()
    #         if ycol < 0: plt.gca().invert_yaxis()
    #         if zcol < 0: plt.gca().invert_yaxis()

    #     # if column names rather than column numbers are provided
    #     if (try_float(split_cols[0]) is False):
    #         xcol = split_cols[0]
    #         ycol = split_cols[1]
    #         zcol = split_cols[2]
    #         ccol = split_cols[3]
    #         type = 'str'

    #     use_columns = 4

    # columns_assigned = True # overwrite control to avoid multiple column assigning
    # arg_nr = i-1 # start ploting from argument 3 to avoid errors when the second arg is cols number

def adjust_ylim(ax=ax1, lower_lim=-16):
    if ax.get_ylim()[0] < -50:
        ax.set_ylim(lower_lim)


def save_plot(filename):
    """
        Save plot

        Parameters:
            filename:       save file under filename.extension
                            if no extension provided, default to '.png'
    """
    plt.savefig(str(filename), dpi=300)

class BlittedCursor:
    """
        A cross-hair cursor using blitting for faster redraw
    """
    def __init__(self, ax):
        self.ax = ax
        self.background = None
        self.horizontal_line = ax.axhline(p[abs(int(ycol))-1][0], color='k', alpha=0.5, lw=0.5, ls='--')
        self.vertical_line =   ax.axvline(p[abs(int(xcol))-1][0], color='k', alpha=0.5, lw=0.5, ls='--')
        # text location in axes coordinates
        self.text = ax.text(0.72, 0.9, '', transform=ax.transAxes)
        self._creating_background = False
        ax.figure.canvas.mpl_connect('draw_event', self.on_draw)

    def on_draw(self, event):
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            # update the line positions
            x, y = event.xdata, event.ydata
            self.horizontal_line.set_ydata([y])
            self.vertical_line.set_xdata([x])
            # self.text.set_text(f'x={x:1.2f}, y={y:1.2f}')

            self.ax.figure.canvas.restore_region(self.background)
            self.ax.draw_artist(self.horizontal_line)
            self.ax.draw_artist(self.vertical_line)
            self.ax.draw_artist(self.text)
            self.ax.figure.canvas.blit(self.ax.bbox)

class Cursor:
    """
        A cross hair cursor.
    """
    def __init__(self, ax, type):
        self.ax = ax
        if type == 'int':
            self.horizontal_line = ax.axhline(p[abs(int(ycol))-1][0], color='k', lw=0.5, alpha=0.5, ls='--')
            self.vertical_line =   ax.axvline(p[abs(int(xcol))-1][0], color='k', lw=0.5, alpha=0.5, ls='--')
        if type == 'str':
            self.horizontal_line = ax.axhline(getattr(p, xcol)[0], color='k', lw=0.5, alpha=0.5, ls='--')
            self.vertical_line =   ax.axvline(getattr(p, ycol)[0], color='k', lw=0.5, alpha=0.5, ls='--')

        # text location in axes coordinates
        self.text = ax.text(0.72, 0.9, '', transform=ax.transAxes)
# p[abs(int(xcol))-1][0], p[abs(int(ycol))-1][0]
    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def on_mouse_move(self, event):
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.draw()
        else:
            self.set_cross_hair_visible(True)
            x, y = event.xdata, event.ydata
            # update the line positions
            self.horizontal_line.set_ydata([y])
            self.vertical_line.set_xdata([x])
            # self.text.set_text(f'x={x:1.2f}, y={y:1.2f}')
            self.ax.figure.canvas.draw()

def search_for_hist(files):
    # numer_of_files = 0
    for i in range(len(files)):
        if os.path.isfile(files[i] + '/LOGS/history.data'):
            file_list.append(files[i] + '/LOGS/history.data')
            # numer_of_files = numer_of_files + 1
        if os.path.isfile(files[i] + '/LOGS1/history.data'):
            file_list.append(files[i] + '/LOGS1/history.data')
            # numer_of_files = numer_of_files + 1
        if os.path.isfile(files[i] + '/LOGS2/history.data'):
            file_list.append(files[i] + '/LOGS2/history.data')
            # numer_of_files = numer_of_files + 1
        if os.path.isfile(files[i] + '/history.data'):
            file_list.append(files[i] + '/history.data')
            # numer_of_files = numer_of_files + 1



### Modular wrapper inserted by refactor ###
# The code block below has been wrapped into a function `plot_all()` so it can be re-used
# for initial draw and for on-demand refresh with the 'a' key.
def plot_all():
    global fig, ax1, ax2, include_legend, if_crosshair_cursor
    global multiplicator, lw, ls, alpha, ms, marker, file, numer_of_files
    global xcol, ycol, p

    ax2 = None

    # jeśli osie już istnieją, czyścimy je
    if ax1 is not None:
        ax1.cla()
        # remove axis-level legend on ax1 if present
        try:
            leg = ax1.get_legend()
            if leg is not None:
                leg.remove()
        except Exception:
            pass
    if ax2 is not None:
        ax2.cla()
        # remove axis-level legend on ax2 if present
        try:
            if hasattr(ax2, 'get_legend'):
                leg2 = ax2.get_legend()
                if leg2 is not None:
                    leg2.remove()
        except Exception:
            pass

    # remove any figure-level legends to avoid duplicates
    try:
        if hasattr(fig, 'legends') and fig.legends:
            for _l in list(fig.legends):
                try:
                    _l.remove()
                except Exception:
                    pass
    except Exception:
        pass


    set_ticks(ax=ax1)

    ### Specify columns to plot ###
    ###############################
    
    # file = str(sys.argv[1])
    # set_ticks(ax=ax1)
    
    search_for_history_file = False
    found_history_file = False
    search_for_columns = False
    columns_assigned = False
    multiple_cols_same_axis = False
    use_size_map = False
    use_color_map = False
    if_save_plot = False
    if_crosshair_cursor = False
    equal_ylim = False
    
    ls = 'solid'
    lw = 4
    marker = None
    ms = 0
    alpha = 0.8
    
    files = sys.argv
    
    for i, arg in enumerate(sys.argv):
    
        if (str(arg) == '-r'):
            search_for_history_file = True
            search_for_hist(file_list)
    
        if (str(arg) == '-ylim'):
            equal_ylim = True
    
        if (str(arg) == '-l'):
            include_legend = True
    
        if (str(arg) == '-/l'):
            include_legend = False        
    
        if (str(arg) == '-c'):
            if_crosshair_cursor = True
    
        if (str(arg) == '-wl'):
            # print('Detected -wl')
            ls = 'solid'
            lw = 4
            ms = 0
            marker = None
            alpha = 0.8
    
        if (str(arg) == '-wp'):
            # print('Detected -wp')
            ls = None
            lw = 0
            ms = 5
            marker = '.'
            alpha = 1.
    
        if (str(arg) == '-wlp' or str(arg) == '-wpl'):
            # print('Detected -wlp')
            ls = 'solid'
            lw = 2
            ms = 10
            marker = '.'
            alpha = 0.7
    
        # if (str(arg) == '-n'):
        #     search_for_columns = True
            
        #     # p = mesa.MesaData(str(file))
        #     # if search_for_history_file:
        #     #     curses.wrapper(data_names,search_for_history_file=True)
        #     #     exit()
        #     # else:
        #     #     curses.wrapper(data_names)
        #     #     exit()
    
        #     executed = False
        #     for i in range(len(files)):
        #         if executed == False:
        #             try:
        #                 p = mesa.MesaData(str(files[i]))
        #                 if search_for_history_file:
        #                     curses.wrapper(data_names,search_for_history_file=True)
        #                     exit()
        #                 else:
        #                     curses.wrapper(data_names)
        #                     exit()
        #                 executed = True
        #             except:
        #                 pass
        #     exit()
        if (str(arg) == '-n'):
            search_for_columns = True
            executed = False  # Flag to check if column analysis has been executed
            
            for file in file_list:  # Iterate over all files from the arguments
                if executed is False:  # Ensure we process only one file
                    try:
                        p = mesa.MesaData(file)  # Attempt to load the file
                        if search_for_history_file:
                            curses.wrapper(data_names, search_for_history_file=True)
                        else:
                            curses.wrapper(data_names)
                        executed = True  # Stop further processing after first file
                    except:
                        continue
            if not executed:
                print("No valid files found to display column names.")
            exit()
    
    
        if (str(arg[0:6]) == '-save='):
            cols = str(sys.argv[i])
            split_save = str.rsplit(cols, sep="=") # split arg like '1:2' for two numbers
            save_file_name = split_save[1]
            if_save_plot = True
            
    
        # specify which cols to plot
        if columns_assigned == False:
            if (str(arg) == 'u' or str(arg) == 'uc' or str(arg) == 'us' or str(arg) == 'mu'):
                columns_assigned = True # overwrite control to avoid multiple column assigning
    
                # determine if to use size/color maps. Requires at least 3 columns to plot
                if (str(arg) == 'uc'): 
                    use_color_map = True
                if (str(arg) == 'us'): 
                    use_size_map = True
    
    
                # if columns ARE provided
                cols = str(sys.argv[i+1])
                split_cols = str.rsplit(cols, sep=":") # split arg like '1:2' for two numbers
    
                if len(split_cols) == 2:
                    # if numbers of columns are provided
                    if (try_float(split_cols[0]) is True):
                        xcol = int(split_cols[0])
                        ycol = int(split_cols[1])
                        type = 'int'
    
                        if xcol < 0: plt.gca().invert_xaxis()
                        if ycol < 0: plt.gca().invert_yaxis()
    
                    # if column names rather than column numbers are provided
                    if (try_float(split_cols[0]) is False):
                        xcol = split_cols[0]
                        ycol = split_cols[1]
                        type = 'str'
    
                    use_columns = 2
    
                if len(split_cols) == 3:
                    # if numbers of columns are provided
                    if (try_float(split_cols[0]) is True):
                        xcol = int(split_cols[0])
                        ycol = int(split_cols[1])
                        zcol = int(split_cols[2])
                        type = 'int'
    
                        if xcol < 0: plt.gca().invert_xaxis()
                        if ycol < 0: plt.gca().invert_yaxis()
                        if zcol < 0: plt.gca().invert_yaxis()
    
                    # if column names rather than column numbers are provided
                    if (try_float(split_cols[0]) is False):
                        xcol = split_cols[0]
                        ycol = split_cols[1]
                        zcol = split_cols[2]
                        type = 'str'
    
                    use_columns = 3
    
                if len(split_cols) == 4:
                    # if numbers of columns are provided
                    if (try_float(split_cols[0]) is True):
                        xcol = int(split_cols[0])
                        ycol = int(split_cols[1])
                        zcol = int(split_cols[2])
                        ccol = int(split_cols[3])
                        type = 'int'
    
                        if xcol < 0: plt.gca().invert_xaxis()
                        if ycol < 0: plt.gca().invert_yaxis()
                        if zcol < 0: plt.gca().invert_yaxis()
    
                    # if column names rather than column numbers are provided
                    if (try_float(split_cols[0]) is False):
                        xcol = split_cols[0]
                        ycol = split_cols[1]
                        zcol = split_cols[2]
                        ccol = split_cols[3]
                        type = 'str'
    
                    use_columns = 4
    
                # columns_assigned = True # overwrite control to avoid multiple column assigning
                arg_nr = i-1 # start ploting from argument 3 to avoid errors when the second arg is cols number
    
            # else:
            #     # if columns ARE NOT provided
            #     arg_nr = 1 # start ploting from argument 1
            #     xcol = 1   # 1, not 0 to avoid errors with the python counting, which starts from 0
            #     ycol = 2   # -||-
            #     type = 'int'
    
            #     use_columns = 2
    
    
            # if (str(arg) == 'uc' or str(sys.argv[i]) == 'us'):
    
    
            # allow for multiple columns to be plotted, e.g. 1:2 3:4...
            if (str(arg) == 'mu'):
    
                xcol = []
                ycol = []
    
                mu_number = 0
    
                for z in range(i, len(sys.argv)):
                    try:
                        cols = str(sys.argv[z+1])
                        split_cols = str.rsplit(cols, sep=":") # split arg like '1:2' for two numbers
    
                        xcol.append(int(split_cols[0]))
                        ycol.append(int(split_cols[1]))
                        type = 'int'
    
                        # print(xcol,ycol)
                        use_columns = 2
                        # print(use_columns)
                        mu_number += 1
                        multiple_cols_same_axis = True
                    except:
                        pass
                # print(use_columns,mu_number,xcol,ycol)
                # while True:
                #     # if columns ARE provided
                #     try:
                #         cols = str(sys.argv[i+1])
                #     except:
                #         pass
                #     # if cols=="": break
    
                #     split_cols = str.rsplit(cols, sep=":") # split arg like '1:2' for two numbers
                #     mu_number =+ 1
    
                #     xcol.append(int(split_cols[0]))
                #     ycol.append(int(split_cols[1]))
    
                #     print(xcol,ycol)
                #     i = i+1
    
                #     # if len(split_cols) == 2:
                #     #     # if numbers of columns are provided
                #     #     if (try_float(split_cols[0]) is True):
                #     #         xcol = int(split_cols[0])
                #     #         append.xcol(int(split_cols[0]))
                #     #         ycol = int(split_cols[1])
                #     #         type = 'int'
    
                #     #         if xcol < 0: plt.gca().invert_xaxis()
                #     #         if ycol < 0: plt.gca().invert_yaxis()
    
                #     #     # if column names rather than column numbers are provided
                #     #     if (try_float(split_cols[0]) is False):
                #     #         xcol = split_cols[0]
                #     #         ycol = split_cols[1]
                #     #         type = 'str'
    
                # columns_assigned = True # overwrite control to avoid multiple column assigning
                arg_nr = i-1 # start ploting from argument 3 to avoid errors when the second arg is cols number
    
    
    
    # colors = plt.cm.jet(np.linspace(0,1,len(sys.argv)-arg_nr))
    # colors = plt.cm.tab20c(np.linspace(0,1,len(sys.argv)-arg_nr))
    # colors = plt.cm.tab20c(np.linspace(0,1))
    # cmap = plt.get_cmap("tab10")
    
    n=-1
    
    if_inverted_axis = False
    is_twin_y = False
    is_colorbar_defined = False
    is_twin_axis_legend_enabled = False
    if_age = False
    
    legend_handles=[]
    
    value_min = None
    value_max = None
    
    # loop for possibly many files to plot
    legend_handles = []
    legend_labels = []
    
    # if '-r' is included in the terminal input, then look for history.data files recursively
    # files = sys.argv
    numer_of_files = 0
    # if search_for_history_file == True: search_for_hist(file_list)
    for i in range(1, len(file_list)):  # Zaczynamy od 1, aby pominąć ścieżkę do skryptu
        if os.path.isfile(file_list[i]):  # Sprawdzamy, czy to plik
            file_to_plot = file_list[i]
            numer_of_files += 1
    
    
    for file in file_list:
        try:
            n=n+1
            if (type == 'int'):
                p = np.loadtxt(file,unpack=True, skiprows=7)
                
                if use_columns == 2:
                    
                    # handle axes labels
                    m = mesa.MesaData(str(file))
    
                    if multiple_cols_same_axis == True:
                        str_y = ''
                        for z in range(0,mu_number): str_y += str(m.bulk_names[abs(int(ycol[z]))-1]) +', '
    
                        ax1.set_xlabel(label_prefix+m.bulk_names[abs(int(xcol[0]))-1],fontsize=fontsize,labelpad=4)
                        ax1.set_ylabel(label_prefix+str_y[:-2],fontsize=fontsize,labelpad=4)
                    else:
                        ax1.set_xlabel(label_prefix+m.bulk_names[abs(int(xcol))-1],fontsize=fontsize,labelpad=4)
                        ax1.set_ylabel(label_prefix+m.bulk_names[abs(int(ycol))-1],fontsize=fontsize,labelpad=4)
    
                    # print('TRY')
                    try:
                        # print(i)
                        if multiple_cols_same_axis == True:
                            for z in range(mu_number):
                                label = file+' '+str(m.bulk_names[abs(int(ycol[z]))-1])
    
                                ax1.plot(p[abs(int(xcol[z]))-1],p[abs(int(ycol[z]))-1]*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=label)
                                # ax1.plot(p[abs(int(xcol[z]))-1],p[abs(int(ycol[z]))-1]*multiplicator, linewidth=0.5, alpha=0.5, c='grey', label=label)
                        else:
                            ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1]*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
                            # ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1]*multiplicator, linewidth=0.5, alpha=0.5, c='grey', label=file)
                            
                            # if file[0:9] == '../single' and 0.0 < float(file[-8:-5]) < 0.4 :
                            #     ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1]*multiplicator, c='tab:blue', linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file, zorder=1)
    
                            # if file[0:6] == 'binary' and 0.0 < float(file[-8:-5]) < 0. :
                            #     ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1]*multiplicator, c='tab:orange', linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file, zorder=10)
                    except:
                        print('\nError loading ' + file + ' file ')
    
                if use_columns == 3 or use_columns == 4: 
                    
                    # handle axes labels
                    m = mesa.MesaData(str(file))
                    ax1.set_xlabel(label_prefix+m.bulk_names[abs(int(xcol))-1],fontsize=fontsize,labelpad=4)
                    ax1.set_ylabel(label_prefix+m.bulk_names[abs(int(ycol))-1],fontsize=fontsize,labelpad=4)
    
    
                    if use_size_map == False and use_color_map == False:
                        if is_twin_y == False: 
                            ax2 = ax1.twinx()
                            set_ticks(ax=ax2)
                            ax2.cla()
                            is_twin_y = True
    
                        ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1], linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
                        ax2.plot(p[abs(int(xcol))-1],p[abs(int(zcol))-1], linewidth=2.0, linestyle='dashed', alpha=alpha, marker=',', ms=ms, label=file, zorder=0.5)
                    
                        ax2.set_ylabel(label_prefix+m.bulk_names[abs(int(zcol))-1],fontsize=fontsize,labelpad=4)
    
                    elif use_size_map == True:
                        plt.tick_params(labelright=False) 
                        if is_twin_y == False: 
                            ax2 = ax1.twinx()
                            set_ticks(ax=ax2)
                            is_twin_y = True
    
                        ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1], linewidth=0.5, alpha=alpha, label=file)
                        value = p[abs(int(zcol))-1]
    
                        # Assign min and max values for the firts entry
                        if value_min is None and value_max is None:
                            value_min = value.min()
                            value_max = value.max()
                        # update min and max values using following entries    
                        elif value_min is not None and value_max is not None:
                            if value.min() < value_min:
                                value_min = value.min()
                            if value.max() > value_max:
                                value_max = value.max()
                        print('%.5f' % value_min, '%.5f' %value_max)
    
                        # normalise values between 0 and 1 and shift to cover range 1 - 30
                        value_norm = (value - value_min)/(value_max - value_min) * 49 + 1 # value.ptp() is equivalent to max - min
                        marker_size = (value_norm).tolist() # s has to be in a list type
                        
    
                        title = label_prefix+m.bulk_names[abs(int(zcol))-1]
                        handles, labels = ax2.scatter(p[abs(int(xcol))-1],p[abs(int(ycol))-1], alpha=alpha, s=marker_size).legend_elements(prop="sizes", alpha=0.6, num=10)
                        # print(handles, labels)
    
                        # label_min = str(p[abs(int(zcol))-1].min())
                        # label_max = str(p[abs(int(zcol))-1].max())
                        label_min = p[abs(int(zcol))-1].min()
                        label_max = p[abs(int(zcol))-1].max()
    
                        labels = ['$\\mathdefault{{%6.3f}}$' % label_min, '$\\mathdefault{}$', '$\\mathdefault{}$', '$\\mathdefault{}$', '$\\mathdefault{}$', '$\\mathdefault{}$', '$\\mathdefault{}$', '$\\mathdefault{}$', '$\\mathdefault{ }$', '$\\mathdefault{{%6.3f}}$' % label_max]
                        # legend_handles.append(handles)
                        # legend_labels.append(labels)
                        ax2.legend(handles, labels, loc="center", title=title, fontsize=sizemap_label_fontsize, title_fontsize=title_fontsize, ncol=len(labels), frameon=False, 
                                       bbox_to_anchor=(0.5, 1.06),markerscale=markerscale)
    
                        # print(i)
    
    
                        # if is_twin_axis_legend_enabled == False: 
                        #     # labels = [labels[0],labels[9]]
                        #     ax2.legend(handles, labels, loc="center", title=title, fontsize=sizemap_label_fontsize, title_fontsize=title_fontsize, ncol=len(labels), frameon=False, 
                        #                bbox_to_anchor=(0.5, 1.06))
                        #     is_twin_axis_legend_enabled = True
    
                        # sizes = ax2.scatter(p[abs(int(xcol))-1],p[abs(int(ycol))-1], alpha=0.7, s=marker_size).legend_elements(prop="sizes", alpha=0.6)
    
                        # kw = dict(prop="sizes", num=5, color=scatter.cmap(0.7), fmt="$ {x:.2f}",
                        #           func=lambda s: np.sqrt(s/.3)/3)
                        # legend2 = ax.legend(*sizes.legend_elements(**kw),
                        #                     loc="lower right", title="Price")
    
                        # print('ok')
                        # ax2.legend(sc.size_map("sizes", num=6))
                        # print('ok2')
                        # if is_twin_axis_legend_enabled == False:
                        #     is_twin_axis_legend_enabled = True
                        #     label = str(label_prefix+m.bulk_names[abs(int(zcol))-1]+':')
    
                        #     size_map_name = ax2.scatter(p[abs(int(xcol))-1][0],p[abs(int(ycol))-1][0], s=1, c='white', label=label)
                        #     ax2.legend(*sc.size_map("sizes", num=2),fontsize=legend_fontsize)
    
                            # size_map_name = ax2.scatter(p[abs(int(xcol))-1][0],p[abs(int(ycol))-1][0], s=1, c='white', label=label)
                            # where_min = np.where(p[abs(int(xcol))-1] == p[abs(int(xcol))-1].min())
                            # size_map_min = ax2.scatter(p[abs(int(xcol))-1][where_min],p[abs(int(ycol))-1][where_min], s=1, label='min')
                            # where_max = np.where(p[abs(int(xcol))-1] == p[abs(int(xcol))-1].max())
                            # size_map_max = ax2.scatter(p[abs(int(xcol))-1][where_max],p[abs(int(ycol))-1][where_max], s=20, label='max')
    
                            # size_map_min = ax2.scatter(p[abs(int(xcol))-1][0],p[abs(int(ycol))-1][0], s=1, label='min')
                            # size_map_max = ax2.scatter(p[abs(int(xcol))-1][0],p[abs(int(ycol))-1][0], s=20, label='max')
    
    
                            # legend_handles=[size_map_name, size_map_min, size_map_max]
                            # ax2.legend(ncol=3,handles=legend_handles,fontsize=legend_fontsize)
                            # ax2.legend(bbox_to_anchor=(1, 1.1),ncol=3,handles=legend_handles,fontsize=legend_fontsize)
    
                            
                            # fig.text(0.5,1,label_prefix,fontsize=fontsize, 
                            #     horizontalalignment='right', verticalalignment='bottom')
                            # plt.text(0.5, 0.95, 'textstr', fontsize=14, transform=plt.gcf().transFigure)
                            
                            # plt.title(r'Size-map enabled. Using MESA.'+m.bulk_names[abs(int(zcol))-1]+' as 3-rd variable.', fontsize=fontsize)
                        # leg = plt.legend(handles=legend_handles, loc=1)# loc=(1.03,0), title="Year")
                        # # ax1.add_artist(leg)
                        # ax = plt.gca().add_artist(leg)
    
    
    
                    # for now only works with one file to plot
                    # elif use_color_map == True:
    
                    #     # ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1], wlp, linewidth=3.0, alpha=0.7, ms=ms, label=file)
                    #     # color = [str(item/255.) for item in p[abs(int(ccol))-1]]
                    #     # ax1.scatter(p[abs(int(xcol))-1],p[abs(int(zcol))-1], c=color)
    
                    #     from matplotlib.collections import LineCollection
                    #     from matplotlib.cm import ScalarMappable
    
                    #     x = p[abs(int(xcol))-1]
                    #     y = p[abs(int(ycol))-1]
                    #     color_axis = p[abs(int(zcol))-1]
    
                    #     # Create a set of line segments so that we can color them individually
                    #     # This creates the points as an N x 1 x 2 array so that we can stack points
                    #     # together easily to get the segments. The segments array for line collection
                    #     # needs to be (numlines) x (points per line) x 2 (for x and y)
                    #     points = np.array([x, y]).T.reshape(-1, 1, 2)
                    #     segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
                    #     # Create a continuous norm to map from data points to colors
                    #     norm = plt.Normalize(color_axis.min(), color_axis.max())
                    #     lc = LineCollection(segments, cmap='inferno', norm=norm, linewidths=3.0, label=file)
                    #     # Set the values used for colormapping
                    #     lc.set_array(color_axis)
                    #     if is_colorbar_defined == False:
                    #         is_colorbar_defined = True
    
                    #         line = ax1.add_collection(lc)
                    #         colorbar = fig.colorbar(line, ax=ax1)
                    #         colorbar.set_label(label_prefix+m.bulk_names[abs(int(zcol))-1],fontsize=fontsize,labelpad=4)
                    #         colorbar.ax1.tick_params(labelsize=fontsize)
    
    
                    #     # ax1.set_xlim(0.9*x.min(), 1.1*x.max())
                    #     # if m.bulk_names[abs(int(xcol))-1]=='model_number':
                    #     #     ax1.set_xlim(0, x.max())
                    #     # else:
                    #     #     ax1.set_xlim(0.9*x.min(), 1.1*x.max())
                    #     # ax1.set_ylim(-1.1, 1.1)
                    #     # plt.show()
    
    
    
    
                    #     # lc = LineCollection(segments_from(p[abs(int(xcol))-1],p[abs(int(ycol))-1]),
                    #     #                     linewidths=2.0,
                    #     #                     norm=norm, cmap=cmap)
                    #     # lc.set_array(p[abs(int(zcol))-1])
                    #     # ax1.add_collection(lc)
    
                    #     # colorbar = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap))
                    #     # colorbar.set_label(r'$\log\ dM/dt\ \rm{[M_{\odot}\ y^{-1}]}$', fontsize=20)
                    #     # colorbar.ax1.tick_params(labelsize=15)
    
    
    
    
                    # # create other y axis assiming that x-axis is shared between data
                    # if is_twin_y == False: 
                    #     ax2 = ax1.twinx()
                    #     set_ticks(ax=ax2)
                    #     is_twin_y = True
    
                    # # handle axes labels
                    # m = mesa.MesaData(str(file))
                    # ax1.set_xlabel(label_prefix+m.bulk_names[abs(int(xcol))-1],fontsize=fontsize,labelpad=4)
                    # ax1.set_ylabel(label_prefix+m.bulk_names[abs(int(ycol))-1],fontsize=fontsize,labelpad=4)
                    # ax2.set_ylabel(label_prefix+m.bulk_names[abs(int(zcol))-1],fontsize=fontsize,labelpad=4)
    
                    
                    # try:
                    #     ax1.plot(p[abs(int(xcol))-1],p[abs(int(ycol))-1], linewidth=lw, linestyle=ls, alpha=0.7, ms=ms, marker=marker, label=file)
                    #     ax2.plot(p[abs(int(xcol))-1],p[abs(int(zcol))-1], linewidth=2.0, linestyle='dashed', alpha=0.7, marker=',', ms=ms, label=file)
                    # except:
                    #     print('\nError loading ' + file + ' file ')
    
            if (type == 'str'):
                if use_columns == 2:
                    
                    p = mesa.MesaData(str(file))
    
                    try:
                        xcol = split_cols[0]
                        ycol = split_cols[1]
    
                        if str(split_cols[0]) == 'log_Teff' and if_inverted_axis == False: 
                            plt.gca().invert_xaxis() 
                            if_inverted_axis = True         # make sure the xaxis gets inverted only once
                        # if str(split_cols[0]) == 'star_age' or str(split_cols[0]) == 'age':
                        #     max_exponent = max([int(f"{x:.1e}".split("e")[1]) for x in getattr(p, xcol)])
                        #     # print(max_exponent)
                        #     if_age = True
    
                        if if_age:
                            ax1.plot(getattr(p, xcol)/10**max_exponent, getattr(p, ycol)*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
                        else:
                            ax1.plot(getattr(p, xcol), getattr(p, ycol)*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
                        # ax1.plot(getattr(p, xcol), getattr(p, ycol), linewidth=lw, linestyle=ls,  alpha=alpha, ms=ms, label=label)
                        # ax1.plot(p.xcol,p.ycol, c=colors[n], linewidth=lw, linestyle=ls, label=file)
    
                        # handle axes labels
                        if if_age:
                            ax1.set_xlabel(fr'star_age [$10^{max_exponent}$ yr]',fontsize=fontsize,labelpad=4)
                        else:
                            ax1.set_xlabel(label_prefix+xcol,fontsize=fontsize,labelpad=4)
                        ax1.set_ylabel(label_prefix+ycol,fontsize=fontsize,labelpad=4)
    
                    except:
                        print('\n  strError - column "%s" or "%s" names not found' %(xcol,ycol))#+str(n)+'\n')
    
                if use_columns == 3:
                    
                    # create other y axis assiming that x-axis is shared between data
                    if is_twin_y == False: 
                        ax2 = ax1.twinx()
                        ax2.cla()
                        set_ticks(ax=ax2)
                        is_twin_y = True
                    # ax2.yaxis.set_minor_locator(AutoMinorLocator())
                    # ax2.tick_params(direction='in', labelsize=labelsize)
                    # ax2.format_coord = make_format(ax2, ax1)
    
                    p = mesa.MesaData(str(file))
                    try:
                        xcol = split_cols[0]
                        ycol = split_cols[1]
                        zcol = split_cols[2]
    
                        if str(split_cols[0]) == 'log_Teff' and if_inverted_axis == False: 
                            plt.gca().invert_xaxis() 
                            if_inverted_axis = True         # make sure the xaxis gets inverted only once
                        # if str(split_cols[0]) == 'star_age' or str(split_cols[0]) == 'age':
                        #     max_exponent = max([int(f"{x:.1e}".split("e")[1]) for x in getattr(p, xcol)])
                        #     # print(max_exponent)
                        #     if_age = True
                        
                        if if_age:
                            ax1.plot(getattr(p, xcol)/10**max_exponent, getattr(p, ycol)*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
                            ax2.plot(getattr(p, xcol)/10**max_exponent, getattr(p, zcol), linewidth=2.0, linestyle='dashed', alpha=alpha, marker=',', ms=ms, label=file, zorder=0.5)
                        else:
                            ax1.plot(getattr(p, xcol), getattr(p, ycol)*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
                            ax2.plot(getattr(p, xcol), getattr(p, zcol), linewidth=2.0, linestyle='dashed', alpha=alpha, marker=',', ms=ms, label=file, zorder=0.5)
                        # ax1.plot(getattr(p, xcol), getattr(p, ycol)*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
                        # ax2.plot(getattr(p, xcol), getattr(p, zcol), linewidth=2.0, linestyle='dashed', alpha=alpha, marker=',', ms=ms, label=file, zorder=0.5)
    
                        # handle axes labels
                        if if_age:
                            ax1.set_xlabel(fr'star_age [$10^{max_exponent}$ yr]',fontsize=fontsize,labelpad=4)
                        else:
                            ax1.set_xlabel(label_prefix+xcol,fontsize=fontsize,labelpad=4)
                        ax1.set_ylabel(label_prefix+ycol,fontsize=fontsize,labelpad=4)
                        ax2.set_ylabel(label_prefix+zcol,fontsize=fontsize,labelpad=4)
                        
                    except:
                        print('\n  strError - column "%s" or "%s" or "%s" names not found' %(xcol,ycol,zcol))#+str(n)+'\n')
    
        except:
            continue
            # print('\nError loading ' + file + ' file ')#+str(n)+'\n')
    
    for arg in sys.argv:
        if use_columns == 2:
            if (str(arg) == '-xlog'): ax1.set_xscale('log')
            if (str(arg) == '-ylog'): ax1.set_yscale('log')
            adjust_ylim(ax=ax1)
        else:
            if (str(arg) == '-xlog'): ax1.set_xscale('log')
            if (str(arg) == '-ylog'): ax1.set_yscale('log')
            if (str(arg) == '-ylog'): ax2.set_yscale('log')
    
        # set min and max bounds for yaxes 
        # print(ax1.get_ylim())
        # print(ax2.get_ylim()[0])
        # if min.ax1 < min.ax2:
    
            if (2. > ax1.get_ylim()[0] / ax2.get_ylim()[0] > 0.5 or 2. > ax2.get_ylim()[0] / ax1.get_ylim()[0] > 0.5 and \
                2. > ax1.get_ylim()[1] / ax2.get_ylim()[1] > 0.5 or 2. > ax2.get_ylim()[1] / ax1.get_ylim()[1] > 0.5 ):
                if ax1.get_ylim()[0] < ax2.get_ylim()[0]: 
                    min_lim_bound = ax1.get_ylim()[0]
                else:
                    min_lim_bound = ax2.get_ylim()[0]
                # if max.ax1 < max.ax2:
                if ax1.get_ylim()[1] < ax2.get_ylim()[1]: 
                    max_lim_bound = ax2.get_ylim()[1]
                else:
                    max_lim_bound = ax1.get_ylim()[1]
                
                ax1.set_ylim(min_lim_bound, max_lim_bound)
                ax2.set_ylim(min_lim_bound, max_lim_bound)
    
            if equal_ylim and len(split_cols) > 2:
                ax2.set_ylim(ax1.set_ylim())
    
            adjust_ylim(ax=ax1)
            adjust_ylim(ax=ax2)
    
    
    
    # ax1.grid(alpha=0.3)
    # ax2.grid(alpha=0.2, linestyle='dashed')
    
    if include_legend:
    # usuń starą legendę, jeśli istnieje
        leg = ax1.get_legend()
        if leg is not None:
            leg.remove()

        if numer_of_files <= 20:
            legend = ax1.legend(loc="best", fontsize=legend_fontsize, markerscale=markerscale)
            # change the line width for the legend, no matter what linewidths are used in the plot
            for line in legend.get_lines():
                line.set_linewidth(legend_linewidth)
        else:
            print("A number of arguments to plot exceed the allowed number to accommodate legend.")
        # plt.tight_layout()
    
    if if_save_plot == True:
        save_plot(save_file_name)
    
    if if_crosshair_cursor == True:
        # Simulate a mouse move to (0.5, 0.5), needed for online docs
        from matplotlib.backend_bases import MouseEvent
        # blitted_cursor = BlittedCursor(ax1)
        # fig.canvas.mpl_connect('motion_notify_event', blitted_cursor.on_mouse_move)
        # cursor = Cursor(ax1)
        # fig.canvas.mpl_connect('motion_notify_event', cursor.on_mouse_move)
    
        # t = ax1.transData
    
        if (type == 'int'):
            # print('int')
            cursor = Cursor(ax1, 'int')
            fig.canvas.mpl_connect('motion_notify_event', cursor.on_mouse_move)
    
            t = ax1.transData
            MouseEvent(
                "motion_notify_event", ax1.figure.canvas, *t.transform((p[abs(int(xcol))-1][0], p[abs(int(ycol))-1][0]))
            )._process()
        elif (type == 'str'):
            # print('str')
            cursor = Cursor(ax1, 'str')
            fig.canvas.mpl_connect('motion_notify_event', cursor.on_mouse_move)
    
            t = ax1.transData
            # ax1.plot(getattr(p, xcol), getattr(p, ycol)*multiplicator, linewidth=lw, linestyle=ls, alpha=alpha, ms=ms, marker=marker, label=file)
            MouseEvent(
                "motion_notify_event", ax1.figure.canvas, *t.transform((getattr(p, xcol)[0], getattr(p, ycol)[0]))
            )._process()
    # p[abs(int(xcol))-1][0], p[abs(int(ycol))-1][0]
    
    # print(numer_of_files)

    # Ensure the title mentions the refresh option once at startup
    try:
        _existing_title = ax1.get_title()
        if "Press [a] to refresh" not in _existing_title:
            ax1.set_title((_existing_title + " | Press [a] to refresh").strip(" |"))
    except Exception as _e:
        pass



# Add refresh interaction: press 'a' to re-load data and redraw without closing the window.
def _on_key(event):
    global fig, ax1, ax2
    if event.key == 'a':
        try:
            if ax1: ax1.cla()
            if ax2 is not None: ax2.cla()
            # Keep annotations about the refresh key at the top
            title = ax1.get_title()
            if "Press [a] to refresh" not in title:
                ax1.set_title((title + " | Press [a] to refresh").strip(" |"))
            plot_all()
            fig.canvas.draw_idle()
        except Exception as e:
            print(f"[refresh] Error while refreshing: {e}")

plot_all()
# Connect key handler
fig.canvas.mpl_connect('key_press_event', _on_key)
### End modular wrapper ###

plt.show()

