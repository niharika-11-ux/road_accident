import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import RandomOverSampler

# Load dataset
df = pd.read_csv('data/road_pred.csv')
features = ['number_of_vehicles','day_of_week','road_type','speed_limit',
            'light_conditions','weather_conditions','road_surface_conditions']
target = 'accident_severity'

# Encode categorical features
encoders = {}
for col in features:
    if df[col].dtype == 'object':
        enc = LabelEncoder()
        df[col] = enc.fit_transform(df[col])
        encoders[col] = enc

# Encode target
target_encoder = LabelEncoder()
df[target] = target_encoder.fit_transform(df[target])

X, y = df[features], df[target]

# Oversample for balanced classes
ros = RandomOverSampler(random_state=42)
X_res, y_res = ros.fit_resample(X, y)

# Train model
model = RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42)
model.fit(X_res, y_res)

# Save model + encoders
pickle.dump(model, open('model/accident_model.pkl', 'wb'))
pickle.dump(encoders, open('model/encoders.pkl', 'wb'))
pickle.dump(features, open('model/feature_order.pkl', 'wb'))
pickle.dump(target_encoder, open('model/target_encoder.pkl', 'wb'))
print("✅ Model trained and saved!")
