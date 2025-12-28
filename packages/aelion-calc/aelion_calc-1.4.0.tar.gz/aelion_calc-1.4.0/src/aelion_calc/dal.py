import math

# ==========================================
# SECTION 1: MONEY & SHOPPING
# ==========================================

def calculate_discount(price, discount_percent):
    """Returns the amount saved."""
    return price * (discount_percent / 100)

def final_price_after_discount(price, discount_percent):
    """Returns the price you actually pay."""
    return price - calculate_discount(price, discount_percent)

def calculate_sales_tax(price, tax_rate_percent):
    """Returns the tax amount."""
    return price * (tax_rate_percent / 100)

def price_with_tax(price, tax_rate_percent):
    """Returns total price including tax."""
    return price + calculate_sales_tax(price, tax_rate_percent)

def split_bill(total_amount, number_of_people, tip_percent=0):
    """
    Calculates how much each person pays.
    Includes an optional tip percentage.
    """
    if number_of_people <= 0: raise ValueError("People must be > 0")
    total_with_tip = total_amount * (1 + tip_percent / 100)
    return round(total_with_tip / number_of_people, 2)

def best_deal(price_a, quantity_a, price_b, quantity_b):
    """
    Compares two products to see which is cheaper per unit.
    Returns string recommending A or B.
    """
    unit_price_a = price_a / quantity_a
    unit_price_b = price_b / quantity_b
    
    if unit_price_a < unit_price_b:
        return f"Option A is cheaper ({unit_price_a:.2f}/unit vs {unit_price_b:.2f}/unit)"
    return f"Option B is cheaper ({unit_price_b:.2f}/unit vs {unit_price_a:.2f}/unit)"

def hourly_wage_to_annual(hourly_rate, hours_per_week=40, weeks_per_year=52):
    """Estimates yearly salary based on hourly wage."""
    return hourly_rate * hours_per_week * weeks_per_year

# ==========================================
# SECTION 2: CAR & TRAVEL
# ==========================================

def fuel_efficiency_mpg(miles, gallons):
    """Calculates Miles Per Gallon (MPG)."""
    return miles / gallons

def fuel_efficiency_kpl(km, liters):
    """Calculates Kilometers Per Liter (KPL)."""
    return km / liters

def trip_cost(distance, fuel_efficiency, gas_price_per_unit):
    """
    Estimates cost of a trip.
    fuel_efficiency: can be MPG or KPL (must match distance unit).
    """
    fuel_needed = distance / fuel_efficiency
    return round(fuel_needed * gas_price_per_unit, 2)

def travel_time(distance, speed):
    """Returns hours needed to travel a distance."""
    return round(distance / speed, 2)

def km_per_liter_to_mpg(kpl):
    """Converts KPL to MPG."""
    return kpl * 2.35215

def mpg_to_km_per_liter(mpg):
    """Converts MPG to KPL."""
    return mpg / 2.35215

# ==========================================
# SECTION 3: HOME & DIY (CONSTRUCTION)
# ==========================================

def paint_required(wall_area_sqft, coverage_per_gallon=350):
    """Calculates gallons of paint needed."""
    return math.ceil(wall_area_sqft / coverage_per_gallon)

def tiles_needed(room_area, tile_area, waste_margin_percent=10):
    """
    Calculates number of tiles needed.
    Adds a percentage for waste/breakage (default 10%).
    """
    raw_count = room_area / tile_area
    total_count = raw_count * (1 + waste_margin_percent / 100)
    return math.ceil(total_count)

def electricity_cost(watts, hours_used, price_per_kwh):
    """
    Calculates cost to run an appliance.
    watts: Power rating of device (e.g., 100W bulb)
    """
    kwh = (watts * hours_used) / 1000
    return round(kwh * price_per_kwh, 2)

def air_conditioner_size_btu(room_sqft):
    """Rough estimate of AC BTU needed for a room."""
    return room_sqft * 20

def carpet_cost(length_ft, width_ft, price_per_sqft):
    return (length_ft * width_ft) * price_per_sqft

# ==========================================
# SECTION 4: COOKING & KITCHEN
# ==========================================

def scale_recipe(amount, current_servings, desired_servings):
    """
    Calculates new ingredient amount when changing serving size.
    Example: Recipe serves 4, you want 8. Input: (200g, 4, 8) -> 400g
    """
    ratio = desired_servings / current_servings
    return amount * ratio

def cups_to_ml(cups): return cups * 236.588
def ml_to_cups(ml): return ml / 236.588
def tbsp_to_tsp(tbsp): return tbsp * 3
def tsp_to_tbsp(tsp): return tsp / 3
def ounces_to_grams(oz): return oz * 28.3495

# ==========================================
# SECTION 5: TIME & PRODUCTIVITY
# ==========================================

def minutes_to_hours(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m"

def seconds_to_hms(seconds):
    """Converts seconds to H:M:S format."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h)}:{int(m):02d}:{int(s):02d}"

def reading_time_minutes(word_count, wpm=200):
    """Estimates reading time (avg speed is 200 words per min)."""
    return math.ceil(word_count / wpm)

def pomodoro_sessions_needed(total_hours, work_session_min=25):
    """Calculates how many Pomodoro sessions fit in a time block."""
    total_minutes = total_hours * 60
    return math.floor(total_minutes / work_session_min)

def sleep_cycles_calculator(wake_time_hours, cycles=5):
    """
    Suggests bed time. A sleep cycle is ~90 mins.
    This is a rough calculator subtracting 90mins * cycles.
    """
    cycle_minutes = 90 * cycles
    return f"You should sleep {cycle_minutes / 60} hours before your alarm."