#!/usr/bin/env python

"""
Functions for annotating and formatting ticklabels (using the class PlotInfo)

@author: Mette Bentsen
@contact: mette.bentsen (at) mpi-bn.mpg.de
@license: MIT
"""

import plotannot.code

def annotate_ticks(ax, axis, labels,
					expand_axis=0,
					rel_label_size=1.1,
					perp_shift=5,
					rel_tick_size=0.25,
					resolution=1000,
					speed=0.1, 
					verbosity=1
					):
	"""
	Annotate ticks with a subset of labels, and shift to overlapping labels.

	Parameters:
	--------------
	ax : matplotlib.axes.Axes
		Axes object holding the plot and labels to annotate.
	axis : str
		Name of axis to annotate. Must be one of ["xaxis", "yaxis", "left", "right", "bottom", "top"].
	labels : list of str
		A list of labels to annotate. Must be a list of strings (or values convertible to strings) corresponding to the labels to show in plot.
	expand_axis : float or tuple, optional
		Expand the annotation axis by this amount of the total axis width. Can be either float or tuple of floats. 
		Corresponds to the relative size of axes to expand with, e.g. 0.1 extends with 5% of the axis size in both directions (total 10%). 
		A tuple of (0.1,0.2) extends the axis with 10% in the beginning (left or bottom) and 20% (right or top). Default: 0.
	rel_label_size : float, optional
		Relative size of labels to use for measuring overlaps. Default: 1.1.
	perp_shift : float, optional
		Perpendicular shift of labels. Represents the relative length of ticks of the axis. Default: 5 (5 times the length of ticks).
	rel_tick_size : float, optional
		Relative size of the horizontal part of the annotation lines as a fraction of perp_shift. Default: 0.25.
	resolution : int, optional
		Resolution for finding overlapping labels. Default: 1000.
	speed : float, optional
		The speed with which the labels are moving when removing overlaps. A float value between 0-1. Default: 0.1.
	verbosity : int, optional
		The level of logging from the function. An integer between 0 and 3, corresponding to: 0: only errors, 1: minimal, 2: debug, 3: spam debug. Default: 1.
	"""

	p = plotannot.code.PlotInfo(ax, verbosity=verbosity)

	p.check_axis(axis)
	p.subset_ticklabels(axis, labels)
	p.extend_axis(axis, expand_axis=expand_axis)
	p.shift_integer_labels(axis, resolution=resolution, rel_label_size=rel_label_size, speed=speed)
	p.apply_shift(axis, perp_shift=perp_shift)
	p.plot_annotation_lines(axis, rel_tick_size=rel_tick_size)


def format_ticklabels(ax, axis, labels=None, format_ticks=False, verbosity=1, **kwargs): 
	"""
	Format ticklabels of a given axis using attributes such as color, fontsize, fontweight, etc.

	Parameters:
	--------------
	ax : matplotlib.axes.Axes
		Axes object holding the plot and labels to annotate.
	axis : str
		Name of axis to annotate. Must be one of ["xaxis", "yaxis", "left", "right", "bottom", "top"].
	labels : list of str, optional
		A list of labels to annotate. Must be a list of strings corresponding to the labels to show in plot. If None, all labels are used. Default: None.
	format_ticks : bool, optional
		If True, also format the ticklines of the axis. Default: False.
	verbosity : int, optional
		The level of logging from the function.  An integer between 0 and 3, corresponding to: 0: only errors, 1: minimal, 2: debug, 3: spam debug. Default: 1.
	kwargs : args, optional
		Additional keyword arguments containing the attributes to set for labels. Each attribute is used as a function "set_" + attribute for the label,
		e.g. "color='red'" will set the color of the label to red using the label-function 'set_color'.
	"""

	p = plotannot.code.PlotInfo(ax, verbosity=verbosity)
	axis = p.format_axis(axis)

	#Check if kwargs were given
	if len(kwargs) == 0:
		raise ValueError("No attributes given to format labels.")
	
	#Apply to axis (can be more than one if axis is "xaxis" or "yaxis")
	for a in axis:

		#Get labels for applying functions
		label_objects = [d["object"] for d in p.label_info[a]]
		tick_objects = [d["object"] for d in p.tick_info[a]]
		
		#Subset to labels if chosen
		if labels is not None:
			labels = [str(l) for l in labels]

			p.check_labels(a, labels)
			indices = [i for i, o in enumerate(label_objects) if o._text in labels]
			label_objects = [label_objects[i] for i in indices] 
			tick_objects = [tick_objects[i] for i in indices]

		#Apply attributes to ticklabels
		for attribute, value in kwargs.items():
			
			func_name = "set_" + attribute
			
			#Format labels
			for label in label_objects:
				try:
					f = getattr(label, func_name)
				except:
					raise ValueError("{func_name}")
				f(value)
			
			#Format ticks
			if format_ticks == True:
				for tick in tick_objects:
					if hasattr(tick, func_name):
						f = getattr(tick, func_name)
						f(value)
