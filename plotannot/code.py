#!/usr/bin/env python

"""
PlotInfo class for plotannot

@author: Mette Bentsen
@contact: mette.bentsen (at) mpi-bn.mpg.de
@license: MIT
"""

import sys
import numpy as np
import matplotlib
import matplotlib.transforms
import matplotlib.pyplot as plt

#Functions for logging
import logging
from logging import ERROR, INFO, DEBUG

#Create additional level below DEBUG
SPAM = DEBUG - 1
logging.addLevelName(SPAM, 'SPAM')

class PlotInfo():
	""" A class collecting information on plot elements to annotate """ 

	def __init__(self, o, verbosity=1):

		self.set_logger(verbosity=verbosity)
		self.get_figure()
		self.get_axis(o)
		self.get_transform()
		self.get_axis_info()
		self.get_tick_info()

	def set_logger(self, verbosity=1):
		""" Set logger for class.
		
		Parameters
		-------------
		verbosity : int
			Verbosity level. An integer between 0 and 3, corresponding to: 0: only errors, 1: minimal, 2: debug, 3: spam debug. Default: 1.
		"""

		verbosity_to_level = {0: ERROR, #silent
								1: INFO,
								2: DEBUG,
								3: SPAM #extreme spam debugging
								} 
		level = verbosity_to_level[verbosity]

		self.verbosity = verbosity
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(level)
		
		#Remove all existing handlers
		for handler in self.logger.handlers:
			self.logger.removeHandler(handler)
		self.logger.addHandler(logging.StreamHandler(sys.stdout))

		#Create custom spam level
		def spam(self, message, *args, **kwargs):
			if self.isEnabledFor(SPAM):
				self._log(SPAM, message, args, **kwargs)
		self.logger.spam = lambda message, *args, **kwargs: spam(self.logger, message, *args, **kwargs)

		#Format
		formatter = logging.Formatter('[%(levelname)s] %(message)s')
		handler = self.logger.handlers[0]
		handler.setFormatter(formatter)

	def get_figure(self):
		""" Get the current figure """

		fig = plt.gcf()
		fig.canvas.draw()

		self.fig = fig
		self.renderer = fig.canvas.get_renderer()


	def get_axis(self, o):
		""" Get xaxis and yaxis objects.
		
		Parameters
		------------
		o : matplotlib.axes.Axes, sns.ClusterGrid
			An object to find xaxis/yaxis objects from.
		"""

		#For sns.heatmap; get axis directly from object
		if hasattr(o, "xaxis") and hasattr(o, "yaxis"):
			self.ax = o
			self.xaxis = o.xaxis
			self.yaxis = o.yaxis

		#For plt plots; get from _axes
		elif hasattr(o, "_axes"):
			self.ax = o._axes
			self.xaxis = self.ax.xaxis
			self.yaxis = self.ax.yaxis
		
		#for sns.clustermap; get from heatmap axes
		elif hasattr(o, "ax_heatmap"):
			self.ax = o.ax_heatmap
			self.xaxis = self.ax.xaxis
			self.yaxis = self.ax.yaxis

		#Todo: search for xaxis/yaxis in dict
		else:
			self.logger.error("Could not find xaxis/yaxis in object")
			sys.exit()

	def get_transform(self):
		"""
		Get transformation objects for figure and data axis.
		"""

		#Transformation between display and inches
		self.trans_fig = self.fig.dpi_scale_trans
		self.trans_fig_inv = self.trans_fig.inverted()

		self.trans_data = self.ax.transData
		self.trans_data_inv = self.trans_data.inverted()

	@staticmethod
	def format_axis(axis):
		""" Convert "xaxis" and "yaxis" names into "bottom", "top", "left", "right" """

		#Establish axis
		if axis == "xaxis":
			axis = ["top", "bottom"]
		elif axis == "yaxis":
			axis = ["left", "right"]

		if isinstance(axis, str):
			axis = [axis]

		return axis
	
	@staticmethod
	def check_axis(axis):
		""" Check that axis is valid """

		valid = ["xaxis", "yaxis", "top", "bottom", "left", "right"]
		if axis not in valid:
			raise ValueError(f"Given axis '{axis}' is not valid. Possible axis are: {valid}")

	@staticmethod
	def check_value(value, vmin=-np.inf, vmax=np.inf, integer=False, name=None):
		""" Check that value is valid based on vmin/vmax"""

		if vmin > vmax:
			raise ValueError("vmin must be smaller than vmax")

		error_msg = None
		if integer == True:
			if not isinstance(value, int):
				error_msg = "The {0} given ({1}) is not an integer, but integer is set to True.".format(name, value)
		else:
			#check if value is any value
			try:
				_ = int(value)
			except:
				error_msg = "The {0} given ({1}) is not a valid number".format(name, value)

		#If value is a number, check if it is within bounds
		if error_msg is None:
			if not ((value >= vmin) & (value <= vmax)):
				error_msg = "The {0} given ({1}) is not within the bounds of [{2};{3}]".format(name, value, vmin, vmax)
		
		#Finally, raise error if necessary:
		if error_msg is not None:
			raise ValueError(error_msg)


	def check_labels(self, axis, labels):
		""" Check whether given labels are valid for axis """

		self.check_axis(axis)
		axis = self.format_axis(axis)

		for a in axis:
			all_label_texts = [d["object"]._text for d in self.label_info[a]] #all label texts found

			not_found = set(labels) - set(all_label_texts)

			#If there are no visible labels at all; pass
			if len(all_label_texts) == 0:
				pass
			
			#If no matches were found
			elif len(not_found) == len(labels):
				self.logger.warning(f"No match could be found between given 'labels' and the {a}-axis ticklabels.")
				self.logger.warning(f"Axis ticklabels are: {all_label_texts[:5]} (...). Given labels are: {labels[:5]}.")
				self.logger.warning("Please check input labels and axis.")
				raise ValueError("No match between given labels and axis ticklabels")

			#If only some matches were found
			elif len(not_found) > 0:
				self.logger.warning(f"{len(not_found)} string(s) from 'labels' were not found in axis ticklabels. These labels were: {list(not_found)}")

	#---------------- Get information of the axes and labels in the plot ----------------#

	def get_axis_info(self):
		""" Get the extent of all axis in inch coordinates """

		self.axis_info = {}

		#Get extent of axis
		ax_bbox = self.ax.get_window_extent(renderer=self.renderer)
		ax_bbox = ax_bbox.transformed(self.trans_fig_inv) #transform from display to inches

		for axis in ["xaxis", "yaxis"]:
			ax_0, ax_1 = (ax_bbox.x0, ax_bbox.x1) if axis == "xaxis" else (ax_bbox.y0, ax_bbox.y1) # in inches
			self.logger.debug(f"Read info for axis: {axis}. Extent is: {ax_0}, {ax_1}")

			self.axis_info[axis] = {"bbox_inch": ax_bbox, "from_inch": ax_0, "to_inch": ax_1, "extent_inch": ax_1-ax_0} #positions in inches

		#Propagate to individual axis
		self.axis_info["bottom"] = self.axis_info["xaxis"]
		self.axis_info["top"] = self.axis_info["xaxis"]
		self.axis_info["left"] = self.axis_info["yaxis"]
		self.axis_info["right"] = self.axis_info["yaxis"]

	def get_tick_info(self):
		"""
		Save information on tick and labels
		"""

		axis_names = ["bottom", "top", "left", "right"]
		
		self.label_info = {a:[] for a in axis_names}
		self.tick_info = {a:[] for a in axis_names}

		#Collect labels and ticks from axis
		for axis in ["xaxis", "yaxis"]:

			ticks = getattr(self, axis).get_major_ticks() #list of tick objects
			for tick in ticks:
				if axis == "xaxis":
					self.label_info["bottom"].append({"object": tick.label1})
					self.tick_info["bottom"].append({"object": tick.tick1line})
					
					self.label_info["top"].append({"object": tick.label2})
					self.tick_info["top"].append({"object": tick.tick2line})

				elif axis == "yaxis":
					self.label_info["left"].append({"object": tick.label1})
					self.tick_info["left"].append({"object": tick.tick1line})
					
					self.label_info["right"].append({"object": tick.label2})
					self.tick_info["right"].append({"object": tick.tick2line})

		self.remove_invisible_labels()

		#Add additional information about sizes and positions
		for axis in axis_names:
			for l in [self.label_info[axis], self.tick_info[axis]]: #for each list
				for d in l:	#for each dict in list

					bbox = d["object"].get_window_extent(self.renderer)
					bbox_inch = bbox.transformed(self.trans_fig_inv) #to inches
					bbox_data = bbox.transformed(self.trans_data_inv) #to data

					para_0, para_1 = (bbox_inch.x0, bbox_inch.x1) if axis in ["top", "bottom"] else (bbox_inch.y0, bbox_inch.y1) # in inches
					perp_0, perp_1 = (bbox_inch.y0, bbox_inch.y1) if axis in ["top", "bottom"] else (bbox_inch.x0, bbox_inch.x1) #perpendicular size in inches

					para_data_0, para_data_1 = (bbox_data.x0, bbox_data.x1) if axis in ["top", "bottom"] else (bbox_data.y0, bbox_data.y1) #parallel size in data coordinates
					perp_data_0, perp_data_1 = (bbox_data.y0, bbox_data.y1) if axis in ["top", "bottom"] else (bbox_data.x0, bbox_data.x1) #in data coordinates

					additional_info = {"bbox": bbox, "from_inch": para_0, "to_inch": para_1, 
										"pos_inch_para": np.mean([para_0, para_1]), "extent_inch_para": para_1-para_0,
										"pos_data_para": np.mean([para_data_0, para_data_1]), "extent_data_para": para_data_1-para_data_0,

										"pos_inch_perp": np.mean([perp_0, perp_1]), "extent_inch_perp": perp_1-perp_0,
										"pos_data_perp": np.mean([perp_data_0, perp_data_1]), "extent_data_perp": perp_data_1-perp_data_0
										}

					d.update(additional_info) #update dict in place

			#Sort from lowest to highest inches positions on axis
			ind_to_sort = np.argsort([d["pos_inch_para"] for d in self.label_info[axis]])
			self.label_info[axis] = [self.label_info[axis][i] for i in ind_to_sort]
			self.tick_info[axis] = [self.tick_info[axis][i] for i in ind_to_sort]


	def remove_invisible_labels(self):
		"""
		Remove invisible labels (and corresponding ticks) from internal info dicts
		"""

		#Remove any invisible labels from the lists
		for axis in self.label_info:
			visible_indices = [i for i, d in enumerate(self.label_info[axis]) if d["object"]._visible == True]
			self.label_info[axis] = [self.label_info[axis][i] for i in visible_indices]
			self.tick_info[axis] = [self.tick_info[axis][i] for i in visible_indices]


	#------------------- Subset and format labels -----------------#

	def subset_ticklabels(self, axis, labels):
		""" Hide any ticklabels not in 'labels'.
		
		Parameters
		------------
		axis :	str
			Name of axis. One of: "xaxis", "yaxis", "top", "bottom", "left", "right". 
		labels : list
			List of labels to keep.
		"""

		labels = [str(label) for label in labels] #convert labels to strings

		self.check_axis(axis)
		self.check_labels(axis, labels)

		axis = self.format_axis(axis)

		#Subset for each axis separately
		found = []
		for a in axis:
			for i, d in enumerate(self.label_info[a]):
				label_text = d["object"]._text
				if label_text not in labels:
					self.label_info[a][i]["object"].set_visible(False)
					self.tick_info[a][i]["object"].set_visible(False)
				else:
					found.append(label_text)

		self.remove_invisible_labels()


 	#-----------------------------------------------------------------------------------#
	#----------------- Functionality for shifting and annotating labels ----------------#
	#-----------------------------------------------------------------------------------#

	def extend_axis(self, axis, expand_axis=0):
		"""
		Extend the size of axis to make room for labels.

		Parameters
		-------------
		axis : str
			Name of axis. One of: "xaxis", "yaxis", "top", "bottom", "left", "right".
		expand_axis : float or tuple
			Expand the axis by this amount. Corresponds to the relative size of axes to expand with, e.g. 0.1 extends with 5% of the axis size in
			both directions. Default: 0.
		"""
		
		self.check_value(expand_axis, name="expand_axis")

		if isinstance(expand_axis, (int, float)):
			expand_axis = (expand_axis/2, expand_axis/2)

		axis = self.format_axis(axis)
		
		#Adjust axis
		for a in axis:
			self.axis_info[a]["from_inch"] -= self.axis_info[a]["extent_inch"] * expand_axis[0] 	#lower
			self.axis_info[a]["to_inch"] += self.axis_info[a]["extent_inch"] * expand_axis[1] 		#higher
			self.axis_info[a]["extent_inch"] = self.axis_info[a]["to_inch"] - self.axis_info[a]["from_inch"]


	def get_integer_positions(self, resolution=1000):
		""" Integer positions of ticks and ticklabels """
		
		#Save integer positions for axis
		self.integer_positions = {}
		for axis in self.label_info:
			self.logger.debug(f"Getting integer positions for labels on {axis} axis")

			#Initialize tick positions in integer space
			n = len(self.label_info[axis])
			text_positions_int = []
			tick_positions_int = []
		
			#Fill in information from each label
			for i in range(n):
				
				#Size and position of label
				label_position = self.label_info[axis][i]["pos_inch_para"]

				#Extent of axes
				ax_start = self.axis_info[axis]["from_inch"]
				ax_extent = self.axis_info[axis]["extent_inch"]

				#Calculate integer values for labels
				label_position_int = int(((label_position - ax_start) / ax_extent) * resolution)

				#make sure that the positions are not out of bounds
				label_position_int = min(label_position_int, resolution) 
				label_position_int = max(label_position_int, 0)
		
				#Fill lists
				tick_positions_int.append(label_position_int)
				text_positions_int.append(label_position_int)


			#Save information for axis
			self.integer_positions[axis] = {"text_pos_int_arr": text_positions_int,
											"tick_pos_int_arr": tick_positions_int}
			
	
	def get_extent_matrix(self, rel_label_size=1, resolution=1000):
		""" Set extent of labels based on widths of labels """

		for axis in self.label_info:

			n = len(self.label_info[axis])
			extent_matrix_int = np.zeros((n, resolution))

			for i in range(n):
				
				label_position_int = self.integer_positions[axis]["text_pos_int_arr"][i] #current position of label
				label_extent = self.label_info[axis][i]["extent_inch_para"] * rel_label_size
				ax_extent = self.axis_info[axis]["extent_inch"]

				#Get extent of label
				extent_half_int = int((label_extent / ax_extent / 2) * resolution)
				extent_start = label_position_int - extent_half_int
				extent_end = label_position_int + extent_half_int

				#Make sure that the positions are not out of bounds
				label_position_int = min(label_position_int, resolution) 
				label_position_int = max(label_position_int, 0)
				extent_start = max(0, extent_start)
				extent_end = min(extent_end, resolution)

				#Fill matrix
				extent_matrix_int[i, extent_start:extent_end+1] = 1

			self.integer_positions[axis]["extent_matrix_int"] = extent_matrix_int

	@staticmethod
	def roll_matrix(matrix, i, shift):
		""" 
		Roll a matrix along ith rows by shift positions.

		Parameters
		-------------
		matrix : numpy.ndarray
			2D array
		i : int
			Index of axis to roll along.
		shift : int
			Number of positions to shift.
		"""
		
		arr = matrix[i]
		rolled = np.roll(arr, shift)
		
		if shift < 0:
			rolled[shift:] = 0 #last values are 0
		else:
			rolled[:shift] = 0 #first values are 0
		
		matrix[i,:] = rolled
		
		return matrix

	def move_elements(self, current_pos_arr, target_pos_arr, extent_matrix, speed=0.1):
		""" Move elements from their current position closer to their target position, given that they must not overlap.
		
		Parameters
		-------------
		current_pos_arr : array
			Current positions of elements.
		target_pos_arr : array
			Target positions of elements.
		extent_matrix : matrix
			Matrix containing the extent of each element.
		speed : integer
			The speed with which the elements move to their target position. Default: 0.1.
		"""

		#Initialize counts
		failed_count = 0 #count of labels which failed to move
		iteration_count = 0
		n = len(current_pos_arr) #number of elements
		resolution = extent_matrix.shape[1]

		speed = max(int(speed * resolution), 1) #make sure that speed is at least 1
		self.logger.debug(f"speed is {speed} (resolution: {resolution})")

		#Shift elements until all elements fail to move
		while failed_count < n:
			
			failed_count = 0 #intialize failed_count for this iteration
			iteration_count += 1 #increment iteration count
			
			#calculate differences
			diff = current_pos_arr - target_pos_arr
			diff_argsort = np.argsort(diff)
			
			#Shift starting with closest
			for i in diff_argsort:
				
				this_label_pos = current_pos_arr[i]
				this_target_pos = target_pos_arr[i]
				this_diff = diff[i]
				self.logger.spam(f"Label with index {i} (pos: {this_label_pos}) is closest to target (pos: {this_target_pos}) with a diff of {this_diff}")
				
				#What direction is the difference?
				shift = 0
				if this_diff > 0: #Difference is positive; shift should be negative (left)

					if i == 0: #if i is 0, there are no labels to the left, and 
						shift = -1 * this_diff #label can move directly to the left

					else:
						#Get next label is to the left
						left_label_pos = current_pos_arr[i-1] #position of the label to the left
						arr = extent_matrix[[i,i-1], :].sum(axis=0)
						possible_shift = sum(arr[left_label_pos:this_label_pos] == 0) #space between left and current label
						self.logger.spam(f"Possible shift without overlap is {possible_shift}")

						shift = min(possible_shift, np.abs(this_diff))
						shift = min(shift, int(np.ceil(shift * speed))) #cap shift at speed
						shift = -1 * shift #shift to the left (-)
						
				else: #difference is negative or 0; shift should be positive (right)

					if (i+1) == n: #if i+1 is n; there are no labels to the right
						shift = this_diff #label can move directly to the right
					
					else:
						#Get next label is to the right
						right_label_pos = current_pos_arr[i+1]
						arr = extent_matrix[[i,i+1]].sum(axis=0)

						possible_shift = sum(arr[this_label_pos:right_label_pos] == 0)
						shift = min(possible_shift, np.abs(this_diff)) #shift to the right (+)
						shift = min(shift, int(np.ceil(shift * speed))) #cap shift at speed
					
				self.logger.spam(f"Trying to shift label by {shift}")
				
				#If shift is 0, label was not moved (=failed to move)
				if shift == 0:
					failed_count += 1
					
				else:
					
					#Try to perform roll of index
					overlap_before = sum(extent_matrix.sum(axis=0) > 1) #positions with more than two labels
					extent_rolled = PlotInfo.roll_matrix(extent_matrix, i, shift)
					overlap_after = sum(extent_rolled.sum(axis=0) > 1)

					if overlap_before - overlap_after == 0: #no changes in overlaps; success
						extent_matrix = extent_rolled #update
						current_pos_arr[i] += shift

					else:
						failed_count += 1
						#print("Failed to move label. Current failed count is: {0}/{1}".format(failed_count, n))
			
			self.logger.debug(f"Finished iteration {iteration_count} of moves: Failed count is {failed_count}/{n}")

		#Make sure positions are within bounds of resolution
		current_pos_arr = np.clip(current_pos_arr, 0, resolution-1)

		return current_pos_arr


	def shift_integer_labels(self, axis, resolution=1000, rel_label_size=1.1, speed=0.1):
		""" Shift labels to not be overlapping .
		
		Parameters
		-------------
		axis : str or list
			Name of axis. 
		resolution : int, optional
			Number of bins in axis. Default: 1000.
		rel_label_size : float, optional
			Relative size of labels. Default: 1.1. 
		speed : float, optional
			The speed with which labels move. Default: 0.1.
		"""
		
		self.check_axis(axis)
		self.check_value(resolution, vmin=1, integer=True, name="resolution")
		self.check_value(rel_label_size, vmin=0, name="rel_label_size")
		self.check_value(speed, vmin=0, vmax=1, name="speed")

		self.get_integer_positions() #get integer arrays for labels
		
		axis = self.format_axis(axis)
		
		#Shift labels across axis
		for a in axis:
			
			if len(self.label_info[a]) == 0:
				continue #no labels to shift for axis

			self.logger.debug("Shifting integer labels on axis: {0}".format(a))
			self.logger.spam("Initial text positions: {0} (...)".format(self.integer_positions[a]["text_pos_int_arr"][:10]))

			#Start by distributing labels across whole axis
			n = len(self.integer_positions[a]["text_pos_int_arr"])
			new_text_positions = np.linspace(0, resolution, n).astype(int)
			self.integer_positions[a]["text_pos_int_arr"] = new_text_positions #update positions array
			self.logger.spam(f"Initial distribution of labels across axis. New positions are: {new_text_positions[:10]} (...)")
			self.get_extent_matrix(resolution=resolution, rel_label_size=rel_label_size) #update label extent after shifting
			

			#--------- Shift labels closer to ticks without overlapping -------#
			extent_matrix = self.integer_positions[a]["extent_matrix_int"]
			text_positions = self.integer_positions[a]["text_pos_int_arr"]
			tick_positions = self.integer_positions[a]["tick_pos_int_arr"]
			
			#Check initial overlaps
			overlap = extent_matrix.sum(axis=0)
			if max(overlap) > 1: #if any position has more than one label
				self.logger.warning("The labels cannot be fit into the range without overlap.")

				#How much space would be needed?
				space_needed = sum(extent_matrix.sum(axis=1))
				resolution = extent_matrix.shape[1]
				
				needed_extend = space_needed / resolution - 1
				self.logger.warning(f"Set 'expand_axis' to at least {needed_extend:.2f} in order to fit labels into the range.")


			##### shift until no longer possible
			new_text_positions = self.move_elements(current_pos_arr=text_positions, 
													target_pos_arr=tick_positions,
													extent_matrix=extent_matrix,
													speed=speed)

			self.logger.spam(f"Done shifting labels on axis {a}. New positions are: {new_text_positions[:10]}")
			
			#Update positions
			self.integer_positions[a]["text_pos_int_arr"] = new_text_positions


	#-------------------------------------------------------------#
	#------------------ Apply changes to plot --------------------#
	#-------------------------------------------------------------#

	def apply_shift(self, axis, perp_shift=5):
		""" Apply the integer shifted labels to plot.
		
		Parameters
		-----------
		axis : str or list
			Axis to apply shift to.
		perp_shift : int, optional
			The amount label shift perpendicular to axis. Default: 5.
		"""

		#Check input
		self.check_value(perp_shift, vmin=0, name="perp_shift")
		axis = self.format_axis(axis)

		for a in axis:

			if len(self.label_info[a]) == 0:
				continue #no labels to shift for axis

			self.logger.debug(f"Applying shift for axis: {a}")

			#Convert integers back to inches
			resolution = self.integer_positions[a]["extent_matrix_int"].shape[1] #width of matrix
			inches_arr = np.linspace(self.axis_info[a]["from_inch"], self.axis_info[a]["to_inch"], resolution)

			text_positions_int = self.integer_positions[a]["text_pos_int_arr"]  #np.clip(text_positions_int, 0, resolution-1)
			text_positions_inch = inches_arr[text_positions_int]

			#Move labels to new positions in inches space
			for i, d in enumerate(self.label_info[a]): #loop over list of dicts

				self.logger.spam(f"Moving tick {i} ({d['object']._text})")

				#Find the perpendicular shift in relation to ticks
				tick_len_inch = self.tick_info[a][i]["extent_inch_perp"]  #tick_bbox_inch.height if axis in ["top", "bottom"] else tick_bbox_inch.width # in inches 
				this_perp_shift = tick_len_inch * perp_shift

				#Decide whether to shift left/right/up/down
				if a in ["bottom", "left"]:
					this_perp_shift = -1 * this_perp_shift

				self.logger.spam(f"Tick is {tick_len_inch:0.3f} inches wide; perpendicular shift will be {this_perp_shift:0.3f}.")
				
				#Get position of shifted label
				old_para = self.label_info[a][i]["pos_inch_para"]
				new_para = text_positions_inch[i]
				d_para = new_para - old_para
				d_perp = this_perp_shift 
				self.logger.spam(f"Parallel location change: {d_para:.3f} ({old_para:.3f} -> {new_para:.3f})")

				#dx/dy in inches
				if a in ["left", "right"]:
					dx, dy = d_perp, d_para
				else:
					dx, dy = d_para, d_perp 
					
				#Apply transformation
				offset = matplotlib.transforms.ScaledTranslation(dx, dy, self.trans_fig) #from inches into display
				label = self.label_info[a][i]["object"]
				label.set_transform(label.get_transform() + offset)

				#Save shifted box
				d["bbox_shifted"] = label.get_window_extent() #now shifted

	def plot_annotation_lines(self, axis, rel_tick_size=0.25):
		""" Plot lines from the original ticks to the newly shifted labels on the plot. """

		self.check_value(rel_tick_size, vmin=0, vmax=1, name="rel_tick_size")
		axis = self.format_axis(axis)

		for a in axis:
			for i in range(len(self.label_info[a])):

				self.logger.spam("Plotting annotation line for tick {}".format(i))

				#Find out how much labels were shifted in data space
				original_label_bbox = self.label_info[a][i]["bbox"].transformed(self.trans_data_inv) #from display to data
				shifted_label_bbox = self.label_info[a][i]["bbox_shifted"].transformed(self.trans_data_inv) #from display to data

				#perpendicular shift of labels; either positive or negative
				if a in ["top", "bottom"]:
					perp_shift_data = shifted_label_bbox.y0 - original_label_bbox.y0 
				else:
					perp_shift_data = shifted_label_bbox.x0 - original_label_bbox.x0  
				
				self.logger.spam("The perpendicular shift of label is: {}".format(perp_shift_data))
					
				#Start position of ticks on the perpendicular axis
				perp_shift_start = self.tick_info[a][i]["pos_data_perp"]
				self.logger.spam(f"The start of tick in data coordinates is: {perp_shift_start:3f}")

				#Shift locations of each line segment in data coordinates (parallel)
				t1 = perp_shift_start + perp_shift_data #perp_shift is already negative if needed
				t2 = t1 - perp_shift_data * rel_tick_size / 2
				t3 = perp_shift_start + perp_shift_data * rel_tick_size / 2
				t4 = perp_shift_start              #location of axis
				
				#New positions in data coordinates
				old_para = self.tick_info[a][i]["pos_data_para"]
				new_para = (shifted_label_bbox.x0 + shifted_label_bbox.x1)/2 if a in ["top", "bottom"] else (shifted_label_bbox.y0 + shifted_label_bbox.y1)/2
						
				#Plot annotation line
				perp_coord = [t1, t2, t3, t4]                         #perpendicular to axis; from label to axis
				para_coord = [new_para, new_para, old_para, old_para] #parallel to axis
				tick_lw = self.tick_info[a][i]["object"].get_markeredgewidth()
				color = self.tick_info[a][i]["object"].get_color() #carry over existing color of tick
				
				#Get axes limits before plotting
				orig_xlim = self.ax.get_xlim()
				orig_ylim = self.ax.get_ylim()

				if a in ["top", "bottom"]:
					self.ax.plot(para_coord, perp_coord, clip_on=False, lw=tick_lw, color=color) #plot from inches coordinates
				else:
					self.ax.plot(perp_coord, para_coord, clip_on=False, lw=tick_lw, color=color) #plot from inches coordinates

				#Set axes limit in case they were changed by plotting
				self.ax.set_xlim(orig_xlim)
				self.ax.set_ylim(orig_ylim)

				#Hide original tick
				self.tick_info[a][i]["object"].set_visible(False)