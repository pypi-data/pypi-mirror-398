import inspect
from . import math_tools
from . import health
from . import cs_basics
from . import dal
from . import say

# Map user-friendly names to actual modules
MODULE_MAP = {
    "math": math_tools,
    "health": health,
    "cs": cs_basics,
    "daily": dal,
    "say": say
}

def _print_header(text):
    print("\n" + "="*40)
    print(f" {text.upper()}")
    print("="*40)

def help_menu():
    """Displays the main menu of the library."""
    _print_header("Aelion Calc - User Manual")
    print("Welcome! Here are the available modules:\n")
    
    print(f"{'KEY':<10} | {'DESCRIPTION'}")
    print("-" * 30)
    print(f"{'math':<10} | Advanced Algebra, Calculus, Matrices")
    print(f"{'health':<10} | BMI, BMR, Nutrition, Fitness")
    print(f"{'cs':<10} | Algorithms, Binary, Logic")
    print(f"{'daily':<10} | Money, Travel, Construction")
    print(f"{'say':<10} | Advanced Printing & Type Check")
    
    print("\nUsage: manual.check('math')")

def check(module_name=None):
    """
    Lists all functions in a specific module.
    Usage: manual.check('health')
    """
    if module_name is None:
        help_menu()
        return

    module_name = module_name.lower()
    
    if module_name not in MODULE_MAP:
        print(f"\n[Error] Module '{module_name}' not found.")
        print(f"Available options: {list(MODULE_MAP.keys())}")
        return

    selected_module = MODULE_MAP[module_name]
    
    _print_header(f"Module: {module_name}")
    
    # Get all functions dynamically
    functions = inspect.getmembers(selected_module, inspect.isfunction)
    
    for name, func in functions:
        # Get the first line of the docstring for the summary
        doc = inspect.getdoc(func)
        summary = doc.split('\n')[0] if doc else "No description available."
        
        # Print function signature (arguments)
        sig = str(inspect.signature(func))
        
        print(f"• {name}{sig}")
        print(f"  -> {summary}\n")

def search(keyword):
    """
    Searches for a function across the entire library.
    Usage: manual.search("bmi")
    """
    _print_header(f"Search Results for: '{keyword}'")
    
    found = False
    keyword = keyword.lower()
    
    for mod_name, mod_obj in MODULE_MAP.items():
        functions = inspect.getmembers(mod_obj, inspect.isfunction)
        
        for name, func in functions:
            if keyword in name.lower():
                print(f"[{mod_name}] {name}{inspect.signature(func)}")
                found = True
                
    if not found:
        print("No functions found matching that keyword.")