# MESAplot
MESAstar / binary plotting tool

**MESA-plotter**
```
    plot opt[u x:y] [lc[x,y]]

        lc                   filename of your light curve containing at least 2 columns  
                             You can pass as many files to plot as you wish

        <u x:y:z>            specify the column numbers to plot (as integer numbers of columns or
                             using their respective names)

        -r                   look for any LOGS*/history.data files therein to plot

        -n                   name module will print available data column names

        -c                   add cross-hair cursor to the plot

        -l / -/l             add / disable legend (disabled by default)

        -wl / -wp / -wlp     plot using lines [default], points, or lines and points

        -xlog / -ylog        apply log scale on the chosen axis

        -ylim                in multiple-plot mode (plotting 3 variables) set the y-axis
                             limits of the twin axis equal to those of the primary axis

        -save=fname          save plot under fname.extension  
                             If no extension is provided, defaults to ".png"
```

**Examples:**

```plot history.data u 1:2 -wl -save=plot.pdf``` - plot columns 1 and 2 from history.data MESA file using lines and save it as plot.pdf

```plot -r u log_Teff:log_L -l``` - search for any LOGS*/history.data files and plot an HR diagram with legend (works for single star and binary outputs)

```plot history.data -n``` - list all column names in the history.data file 
