
# ml_predictor.py - ADD THIS TO YOUR PROJECT
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

class TrainDelayPredictor:
    """AI-powered delay prediction using machine learning"""

    def __init__(self):
        # Pre-trained model coefficients (from your training)
        self.model = LinearRegression()
        # These coefficients come from training on historical data
        self.model.coef_ = np.array([0.05800074103974408, -0.16898453665102847, -9.117846259335929, -10.291317245298249, 1.2890512888585146, 0.008465044711167023])
        self.model.intercept_ = 19.470161811664518

    def predict_delay(self, hour_of_day, day_of_week, weather_score=0.8, 
                     section_congestion=0.5, train_priority=3, base_speed=100):
        """
        Predict train delay using AI/ML model

        Args:
            hour_of_day: 0-23
            day_of_week: 0-6 (Monday=0)
            weather_score: 0.3-1.0 (0.3=bad weather, 1.0=good)
            section_congestion: 0.2-1.0 (utilization level)
            train_priority: 1-5 (1=highest priority)
            base_speed: train speed in kmph

        Returns:
            predicted_delay_minutes: float
        """
        features = np.array([[hour_of_day, day_of_week, weather_score, 
                            section_congestion, train_priority, base_speed]])

        delay = self.model.predict(features)[0]
        return max(0, delay)  # No negative delays

    def predict_multiple_trains(self, trains_data):
        """Predict delays for multiple trains"""
        predictions = []
        for train_data in trains_data:
            delay = self.predict_delay(**train_data)
            predictions.append(delay)
        return predictions

    def get_risk_assessment(self, predicted_delay):
        """Convert delay to risk level"""
        if predicted_delay < 5:
            return "LOW"
        elif predicted_delay < 15:
            return "MEDIUM" 
        else:
            return "HIGH"

# Usage example:
# predictor = TrainDelayPredictor()
# delay = predictor.predict_delay(hour_of_day=8, train_priority=1)
# print(f"Predicted delay: {delay:.1f} minutes")
