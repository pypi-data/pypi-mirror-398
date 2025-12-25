Version 0.2.16 - released 22-Dec-2025 (Canberra, Australia)

* minor changes
    - added zorder kwarg to line_plot(), bar_plot(), and fill_between_plot()
    - zorder supports sequences for per-series values in multi-series plots
    - added test/test_zorder.py

---

Version 0.2.15 - released 15-Dec-2025 (Canberra, Australia)

* minor changes
    - added suptitle kwarg to finalise_plot() for setting fig.suptitle()
    - suptitle takes priority over title for save-to filename if present

---

Version 0.2.14 - released 10-Dec-2025 (Canberra, Australia)

* bug fix
    - fixed x-axis ticks not spanning full data range when plotting multiple
      series with different time spans on the same axes
    - added test/test_multi_series_ticks.py

---

Version 0.2.13 - released 06-Dec-2025 (Canberra, Australia)

* minor changes
    - added fill_between_plot() function wrapping matplotlib's fill_between
    - added fill_between_plot_finalise() convenience function
    - added FillBetweenKwargs TypedDict

---

Version 0.2.12 - released 26-Jul-2025 (Canberra, Australia)

* minor changes
    - version bump to 0.2.12
    - added label_rotation parameter to BarKwargs for controlling x-axis label rotation
    - documentation updates

---

Version 0.2.11 - released 20-Jul-2025 (Canberra, Australia)

* minor changes
    - version bump to 0.2.101
    - updates to postcovid_plot.py (further gnarly edge cases fixed)

---
Version 0.2.10 - released 20-Jul-2025 (Canberra, Australia)

* minor changes
    - version bump to 0.2.10
    - updates to postcovid_plot.py
    - documentation updates

---

Version 0.2.9 - released 19-Jul-2025 (Canberra, Australia)

* minor changes
    - renamed build-test.sh to build-all.sh
    - version bump to 0.2.9
    - minor code refactoring in postcovid_plot.py

---

Version 0.2.8 - released 18-Jul-2025 (Canberra, Australia)

* minor changes
    - added lint-all.sh script
    - refinements to utilities.py
    - minor code improvements in bar_plot.py, line_plot.py, and finalisers.py
    - documentation updates

---

Version 0.2.7 - released 17-Jul-2025 (Canberra, Australia)

* major changes
    - intensive code linting across all modules
    - significant refactoring in finalisers.py, multi_plot.py, and other core modules
    - improved code quality and consistency
    - documentation regenerated

---

Version 0.2.6 - released 15-Jul-2025 (Canberra, Australia)

* minor changes
    - fixed a glitch where an axhspan was not appearing
      in nthe legend.

---

Version 0.2.5 - released 22-Jun-2025 (Canberra, Australia)

* minor changes
    - Fixed the xlabel thing in finalise_plot().
    - Changed from using Series.plot() to Axes.plot(),
      in line_plot() to avoid pandas setting the 
      xlabel/ylabel
    - fixed a labelling error in summary_plot()
    - removed an imposed-legend from run_plot_finalise()
    - added the capacity to label the runs in the run_plot() legend.
    - small number of consequential changes.

---

Version 0.2.4 - released 21-Jun-2025 (Canberra, Australia)

* minor changes
    - Implemented more aggressive code linting in ruff.
      with all but a handful of ruff linting rules
      activated (see pyproject.toml and lint-all.sh)
    - retired pylint and black

---

Version 0.2.1 - released 19-Jun-2025 (Canberra Australia)

* minor changes
    - changed linting regime - resulted in numerous minor 
      changes.
    - other minor changes

---

Version 0.2.0 - released 18-Jun-2025 (Canberra Australia)

* minor changes
    - fixed a glitch with the scaled summary plot

---

Version 0.2.0a2 - released 18-Jun-2025 (Canberra Australia)

* major changes
    - rewrote dynamic type-checking, to leverage static type 
      definitions
    - enhanced static type information for kwargs in most cases
    - moved test code into a separate directory
    - unresolved issue with scaled z-score charts

---

Version 0.1.13 - released 15-Jun-2025 (Canberra Australia)

* major changes
    - changed xticks for PeriodIndex in line_plot, to do the 
      same as bar_plot().
    - Now all PeriodIndex charts should use this approach to
      the x-axis.

---
Version 0.1.12 - released 14-Jun-2025 (Canberra Australia)

* minor changes
    - chnaged default_rounding() to apply for negative numbers

---

Version 0.1.11 - released 11-Jun-2025 (Canberra Australia)

* minor changes
     - refinements to the build code.

---

Version 0.1.10 - released 11-Jun-2025 (Canberra, Australia)

* minor changes
     - refined transition argument checking.

---

Version 0.1.9 - released 11-Jun-2025 (Canberra, Australia)

* minor changes
     - added some limited type checking through the argument
       transitions in growth_plot(), although most of the
       code is in the kw_type_checking module.

---

Version 0.1.9 - released 10-Jun-2025 (Canberra, Australia)

* minor changes
     - code linting

---

Version 0.1.8 - released 10-Jun-2025 (Canberra, Australia)

* major changes
     - standardised keyword argument names (in a separate module).
     - provided abbreviations for some keyword argument names.
     - removed legend keyword argument from data plotting functions 
       (ie. it is only implemented by finalise_plot())

---

Version 0.1.7 - released 06-Jun-2025 (Canberra, Australia)

* major changes
     - reworked growth_plot so that it used the line_plot()
       and bar_plot() functions. 

---

Version 0.1.6 - released 03-Jun-2025 (Canberra, Australia)

* minor changes
     - sorted the three remaining pylint issues with the 
       kw_type_checking module. Also improved error
       messages in the same module. 

---

Version 0.1.5 - released 02-Jun-2025 (Canberra, Australia)

* minor changes
     - minor changes to pyproject.toml and build-test.sh

---

Version 0.1.4 - released 01-Jun-2025 (Canberra, Australia)

* minor changes
     - changed the build-system
     - added dynamic version numbering to __init__.py
     - reworked annotations in the growth_plot.py module
       and the utilities module,
     - reworked kwargs validation in plot_then_finalise() 
     - typo in kw_type_checking.py
     - tightened up function chaining in the multi-plot modules
     - moved some default arguments from the finalisers module
       to the line_plot module.
     
---

Version 0.1.3 - released 31-May-2025 (Canberra, Australia)

* minor changes
     - changed defaults for postcovid_plot() to annotate series
     - changed line_plot() to bail early if nothing to plot
     - added a test to ignore empty axes objects in finalise_plot()
     - reduced the text size for runs in run_plot()
     - added "legend" to line_plot() and the growth plots.
     - if the plot function and the finalise_plot() function have
       kwargs in common, they will be handled by plot() and not
       sent to finalise plot (done by plot_then_finalise())
---

Version 0.1.2 - released 30-May-2025 (Canberra, Australia)

* minor changes
     - fixed an incorrect typing-gate in run_plot()
     - removed repeated version code in __init__.py
     - added "numpy-typing" to pyproject.toml
     - added a warning if ylabel set in series_growth_plot_finalise()
     - added legend=True default argument to raw_growth_plot()
---

Version 0.1.1 - released 29-May-2025 (Canberra, Australia)

* minor changes
     - added additional documentation
     - disclosed additional variables in the API
     - standardised the naming of the internal ExpectedTypeDicts
---

Version 0.1.0 - released 28-May-2025 (Canberra, Australia)

---
