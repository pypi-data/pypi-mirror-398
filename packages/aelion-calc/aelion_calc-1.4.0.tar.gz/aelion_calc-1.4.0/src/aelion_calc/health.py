import math
import datetime

# ==========================================
# SECTION 1: CORE BODY METRICS
# ==========================================

def calculate_bmi(weight_kg, height_m):
    """Calculates Body Mass Index."""
    if height_m <= 0: raise ValueError("Height must be > 0")
    return round(weight_kg / (height_m ** 2), 2)

def bmi_category(bmi):
    """Returns standard WHO category."""
    if bmi < 18.5: return "Underweight"
    if bmi < 25: return "Normal weight"
    if bmi < 30: return "Overweight"
    if bmi < 35: return "Obesity Class I"
    if bmi < 40: return "Obesity Class II"
    return "Obesity Class III"

def waist_to_hip_ratio(waist, hip):
    """
    Assesses health risk based on fat distribution.
    High risk: > 0.90 (Men), > 0.85 (Women)
    """
    return round(waist / hip, 2)

def body_surface_area(weight_kg, height_cm):
    """
    Mosteller Formula. Used in medicine for dosages.
    Returns area in square meters.
    """
    return round(math.sqrt((weight_kg * height_cm) / 3600), 2)

# ==========================================
# SECTION 2: METABOLISM & ENERGY
# ==========================================

def bmr_mifflin_st_jeor(weight_kg, height_cm, age, gender):
    """
    The 'Gold Standard' for calculating Basal Metabolic Rate.
    gender: 'male' or 'female'
    """
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender.lower() == 'male':
        return int(base + 5)
    return int(base - 161)

def tdee(bmr, activity_level):
    """
    Total Daily Energy Expenditure.
    Levels: 'sedentary', 'light', 'moderate', 'active', 'athlete'
    """
    multipliers = {
        'sedentary': 1.2,      # Desk job
        'light': 1.375,        # Exercise 1-3 days/week
        'moderate': 1.55,      # Exercise 3-5 days/week
        'active': 1.725,       # Exercise 6-7 days/week
        'athlete': 1.9         # Physical job or 2x training
    }
    return int(bmr * multipliers.get(activity_level.lower(), 1.2))

# ==========================================
# SECTION 3: BODY FAT ESTIMATION (NAVY METHOD)
# ==========================================

def body_fat_navy_male(waist_cm, neck_cm, height_cm):
    """
    US Navy Method for Men.
    Accurate within ~3-4% of DEXA scans.
    """
    return round(86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76, 1)

def body_fat_navy_female(waist_cm, hip_cm, neck_cm, height_cm):
    """US Navy Method for Women."""
    return round(163.205 * math.log10(waist_cm + hip_cm - neck_cm) - 97.684 * math.log10(height_cm) - 78.387, 1)

def ideal_weight_miller(height_cm, gender):
    """
    Estimates ideal weight based on height.
    """
    height_in = height_cm / 2.54
    if gender.lower() == 'male':
        return round(56.2 + 1.41 * (height_in - 60), 1)
    return round(53.1 + 1.36 * (height_in - 60), 1)

# ==========================================
# SECTION 4: NUTRITION & MACROS
# ==========================================

def calculate_macros(calories, goal='balanced'):
    """
    Returns grams of Protein, Fat, Carbs.
    Goals: 'balanced', 'low_carb', 'high_protein', 'keto'
    """
    # Ratios: (Protein, Fat, Carbs)
    ratios = {
        'balanced': (0.30, 0.35, 0.35),
        'low_carb': (0.40, 0.40, 0.20),
        'high_protein': (0.45, 0.25, 0.30),
        'keto': (0.25, 0.70, 0.05)
    }
    p, f, c = ratios.get(goal, ratios['balanced'])
    
    return {
        "protein_g": int((calories * p) / 4),
        "fats_g": int((calories * f) / 9),
        "carbs_g": int((calories * c) / 4)
    }

def water_intake_liters(weight_kg, activity_minutes=0, climate='temperate'):
    """
    Calculates daily hydration needs.
    Adds water for exercise and hot climates.
    """
    base = weight_kg * 0.033
    activity_add = (activity_minutes / 30) * 0.35
    climate_add = 0.5 if climate == 'hot' else 0
    return round(base + activity_add + climate_add, 2)

# ==========================================
# SECTION 5: FITNESS & PERFORMANCE
# ==========================================

def karvonen_heart_rate(age, resting_hr, intensity_percent):
    """
    More accurate than (220-age). Uses Heart Rate Reserve.
    intensity_percent: 0.50 to 0.85 usually.
    """
    max_hr = 220 - age
    reserve = max_hr - resting_hr
    target = (reserve * intensity_percent) + resting_hr
    return int(target)

def one_rep_max_epley(weight_lifted, reps):
    """Estimates the max weight you can lift once."""
    if reps == 1: return weight_lifted
    return int(weight_lifted * (1 + (reps / 30)))

def vo2_max_estimate(resting_hr, age):
    """
    Simple estimate (Uth-Sørensen-Overgaard-Pedersen estimation).
    """
    max_hr = 220 - age
    return round(15.3 * (max_hr / resting_hr), 1)

# ==========================================
# SECTION 6: SLEEP ARCHITECTURE
# ==========================================

def calculate_sleep_cycles(wake_time_str, cycles=5):
    """
    Calculates bed time counting backwards by 90-min cycles.
    wake_time_str format: "HH:MM" (24 hour)
    """
    try:
        wake = datetime.datetime.strptime(wake_time_str, "%H:%M")
        minutes_to_sleep = cycles * 90 + 15  # +15 mins to fall asleep
        bed_time = wake - datetime.timedelta(minutes=minutes_to_sleep)
        return bed_time.strftime("%H:%M")
    except ValueError:
        return "Invalid time format. Use HH:MM"

# ==========================================
# SECTION 7: CLINICAL (EDUCATIONAL ONLY)
# ==========================================

def iv_drip_rate(volume_ml, time_hours, drop_factor=20):
    """
    Calculates drops per minute (gtt/min).
    drop_factor: usually 10, 15, 20 (standard), or 60 (micro).
    """
    minutes = time_hours * 60
    return round((volume_ml * drop_factor) / minutes)

def child_dosage_youngs(adult_dose, age_years):
    """
    Young's Rule for child dosage approximation.
    (Age / (Age + 12)) * Adult Dose
    """
    return round((age_years / (age_years + 12)) * adult_dose, 2)