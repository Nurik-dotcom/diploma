import joblib
import numpy as np
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'fraud_model_balanced.pkl')
fraud_model = joblib.load(MODEL_PATH)

features_order = [
    'amount',
    'days_since_signup',
    'transactions_last_hour',
    'transactions_last_day',
    'transactions_last_week',
    'avg_transaction_amount',
    'suspicious_transactions_count',
    'max_transaction_amount_day',
    'failed_transactions_today',
    'incoming_outgoing_ratio'
]

def predict_fraud(features_dict):
    features_array = np.array([features_dict[feature] for feature in features_order]).reshape(1, -1)
    risk_probability = fraud_model.predict_proba(features_array)[0][1] * 100
    return risk_probability
