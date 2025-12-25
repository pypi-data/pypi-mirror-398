mgplot
======

Description
-----------
mgplot is an open-source python frontend for the matplotlib 
package to:
1. produce time-series charts that can be a little difficult or 
   tricky to produce directly, 
2. finalise (or publish) charts with titles, xlabels, ylabels,
   etc., all while 
3. minimising code duplication, and maintaining a common plot
   style or look-and-feel.

Import
------
```
import mgplot as mg
```

Quick overview
--------------
The primary plotting functions take a pandas Series and/or DataFrame
as the first argument. They all return a matplotlib Axes object. 
The remaining arrguments are passed as keyword arguments:
- bar_plot() -- vertical bar plot (managers PeriodIndex date data
  so that not every column is labeled on the plot)
- line_plot() -- one or more lines are ploted.
- postcovid_plot() -- charts the data as a line, with a simple
  linear regression to show the pre-covid trend.
- revision_plot() -- designed to plot a dataframe of ABS revisions.
- run_plot() -- plots a line for a series, with background highlighting
  for increasing and/or decreasing runs.
- seastrend_plot() -- plots seasonal and trend data on the one plot.
- series_growth_plot() -- combines annual and quarterly/monthly 
  growth on the same plot using a line for annual growth and bars
  for quarterly growth.
- summary_plot() -- plots the latest data in a summary-format against
  the range of previous data. 

Once a plot has been generated and an Axes object is available. The
plot can be finalised or published, with appropriate titles and
axis labels using
- finalise_plot()

You can chain the development of plots together with functions designed 
for this purpose. In addition to a required data argument, each of 
these functions also has a required function argument which is either 
a single function or a list of functions.
- multi_start() -- takes a starts argument, and calls the next function
  (repeatedly if necessary) with the plot_from argument set to the one 
  or more starts provided.
- multi_column() -- calls the next function repeatedly, with the data
  set to a single column of its DataFrame.
- plot_the_finalise() -- calls the specified plot function, and then 
  calls the finalise_plot() function.

Finally, for every plot function above, there is a convenience function
that automatically calls both the plot function and then the finalise_plot()
function:
- bar_plot_finalise() -- calls bar_plot() then finalise_plot()
- line_plot_finalise()
- postcovid_plot_finalise()
- revision_plot_finalise()
- run_plot_finalise()
- seastrend_plot_finalise()
- series_growth_plot_finalise()
- summary_plot_finalise()

For more details, see the documentation folder.

---
