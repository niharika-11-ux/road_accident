import pandas as pd
import random

# Possible values
days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
roads = ['Single carriageway','Dual carriageway','Roundabout','One way street']
lights = ['Daylight','Darkness - lights lit','Darkness - no lighting']
weather = ['Fine no high winds','Raining no high winds','Raining with high winds',
           'Snowing no high winds','Snowing with high winds']
surfaces = ['Dry','Wet / Damp','Snow','Frost / Ice']

def determine_severity(row):
    # Fatal
    if (row['speed_limit'] >= 80 
        and row['light_conditions'] != 'Daylight'
        and row['weather_conditions'] in ['Raining with high winds','Snowing with high winds']):
        return 'Fatal'
    
    # Serious
    elif ((50 <= row['speed_limit'] < 80 and row['weather_conditions'] in [
            'Raining no high winds','Raining with high winds','Snowing no high winds','Snowing with high winds'])
          or (row['speed_limit'] >= 70 and row['road_type'] in ['Single carriageway','Roundabout'])
          or (row['speed_limit'] >= 60 and row['road_surface_conditions'] in ['Snow','Frost / Ice'])):
        return 'Serious'
    
    # Slight
    else:
        return 'Slight'

# Generate 5000 samples
data = []
for _ in range(5000):
    row = {
        'number_of_vehicles': random.randint(1,5),
        'day_of_week': random.choice(days),
        'road_type': random.choice(roads),
        'speed_limit': random.choice([30,40,50,60,70,80,90]),
        'light_conditions': random.choice(lights),
        'weather_conditions': random.choice(weather),
        'road_surface_conditions': random.choice(surfaces)
    }
    row['accident_severity'] = determine_severity(row)
    data.append(row)

df = pd.DataFrame(data)
df.to_csv('data/road_pred.csv', index=False)
print("✅ Dataset generated: data/road_pred.csv")
print(df['accident_severity'].value_counts())
