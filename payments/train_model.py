import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

df = pd.read_csv(os.path.join(os.path.dirname(__file__), "transactions_dataset_advanced.csv"))

features = [
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

X = df[features]
y = df['is_suspicious']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

model = GradientBoostingClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

joblib.dump(model, 'fraud_model_balanced.pkl')
