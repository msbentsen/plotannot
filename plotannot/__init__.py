from importlib import import_module

__version__ = "0.1.0"

#Set functions to be available directly, i.e. "from plotannot import annotate"
module = import_module("plotannot.functions")
function_names = [func for func in dir(module) if callable(getattr(module, func)) and not func.startswith("__")]
global_functions = ["plotannot.functions." + s for s in function_names]

for f in global_functions:
	
	module_name = ".".join(f.split(".")[:-1])
	attribute_name = f.split(".")[-1]
	
	module = import_module(module_name)
	attribute = getattr(module, attribute_name)
	
	globals()[attribute_name] = attribute