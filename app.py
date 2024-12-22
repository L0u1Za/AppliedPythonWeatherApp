import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# Function to fetch current weather data from OpenWeatherMap API
def get_current_temperature(city, api_key):
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }
    response = requests.get('http://api.openweathermap.org/data/2.5/weather', params=params)
    return response.json()

# Streamlit App
st.title("Weather Data Analysis and Current Weather Checker")

# File upload for historical data
st.sidebar.header("Upload Historical Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file with columns: city, timestamp, temperature, season")
if uploaded_file:
    data = pd.read_csv(uploaded_file)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    st.sidebar.success("File uploaded successfully!")

    # City selection
    city_list = data['city'].unique().tolist()
    selected_city = st.sidebar.selectbox("Select a city:", city_list)

    # Filter data for selected city
    city_data = data[data['city'] == selected_city]

    # Descriptive statistics
    st.header(f"Descriptive Statistics for {selected_city}")
    st.write(city_data.describe())

    # Seasonal statistics
    st.subheader("Seasonal Profiles")
    seasonal_stats = city_data.groupby('season')['temperature'].agg(['mean', 'std']).reset_index()
    seasonal_stats.rename(columns={'mean': 'avg_temperature', 'std': 'std_temperature'}, inplace=True)
    st.write(seasonal_stats)

    # Plotting seasonal profiles
    fig, ax = plt.subplots()
    ax.bar(seasonal_stats['season'], seasonal_stats['avg_temperature'], yerr=seasonal_stats['std_temperature'], capsize=5)
    ax.set_title(f"Seasonal Temperature Profiles for {selected_city}")
    ax.set_ylabel("Temperature (°C)")
    st.pyplot(fig)

    # Time series plot with anomalies
    rolling_avg = city_data['temperature'].rolling(window=30, min_periods=1).mean()
    rolling_std = city_data['temperature'].rolling(window=30, min_periods=1).std()
    upper_bound = rolling_avg + 2 * rolling_std
    lower_bound = rolling_avg - 2 * rolling_std
    city_data['is_anomaly'] = (city_data['temperature'] > upper_bound) | (city_data['temperature'] < lower_bound)

    fig, ax = plt.subplots()
    ax.plot(city_data['timestamp'], city_data['temperature'], label='Temperature', marker='o')
    ax.fill_between(city_data['timestamp'], lower_bound, upper_bound, color='gray', alpha=0.2, label='±2σ Range')
    plt.scatter(city_data['timestamp'][city_data['is_anomaly']],
            city_data['temperature'][city_data['is_anomaly']],
            color='red', label='Anomalies', zorder=5)
    ax.set_title(f"Temperature Time Series and Anomalies for {selected_city}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature (°C)")
    ax.legend()
    st.pyplot(fig)

# API Key input for OpenWeatherMap
st.sidebar.header("Current Weather")
api_key = st.sidebar.text_input("Enter your OpenWeatherMap API Key:")

def is_anomaly(cur_temp, season):
  cur_norm_temp = seasonal_stats[seasonal_stats['season'] == season]
  avg_temp, std_temp = cur_norm_temp['avg_temperature'].values[0], cur_norm_temp['std_temperature'].values[0]
  return (cur_temp < avg_temp - 2 * std_temp) | (cur_temp > avg_temp + 2 * std_temp)

month_to_season = {12: "winter", 1: "winter", 2: "winter",
                   3: "spring", 4: "spring", 5: "spring",
                   6: "summer", 7: "summer", 8: "summer",
                   9: "autumn", 10: "autumn", 11: "autumn"}

def get_season():
    current_month = datetime.now().month
    return month_to_season[current_month]


if api_key:
    try:
        current_weather = get_current_temperature(selected_city, api_key)

        if current_weather.get("cod") == 401:
            st.sidebar.error("Invalid API key. Please see https://openweathermap.org/faq#error401 for more info.")
        else:
            current_temp = current_weather['main']['temp']
            st.sidebar.success(f"Current temperature in {selected_city}: {current_temp} °C")

            # Compare current temperature to seasonal profile
            current_season = get_season()
            if is_anomaly(current_temp, current_season):
                st.sidebar.warning("The current temperature is unusual for this season.")
            else:
                st.sidebar.info("The current temperature is within the normal range for this season.")
    except Exception as e:
        st.sidebar.error(f"Error fetching weather data: {str(e)}")
