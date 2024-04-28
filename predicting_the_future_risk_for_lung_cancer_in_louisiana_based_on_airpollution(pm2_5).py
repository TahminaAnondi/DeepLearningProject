# -*- coding: utf-8 -*-
"""Predicting_The_Future_Risk_For_Lung_Cancer_in_Louisiana_Based_on_AirPollution(PM2.5)

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Lwy9SBD_jlR5f6_TKS6LxPz963WdORRm
"""

#Import Libraries
import tensorflow as tf
import numpy as np #Linear Algebra
import matplotlib.pyplot as plt #Data visualization
import pandas as pd #data manipulation

import warnings
warnings.filterwarnings('ignore') #Ignore warnings

#Make sure Tensorflow is version 2.0 or higher
print('Tensorflow Version:', tf.__version__)

import pandas as pd

# Assuming 'pollution' DataFrame is filtered for desired time period and city
# Replace these lines with your actual code to load and filter the data
pollution = pd.read_csv("/content/AirPollution.xlsx - Sheet5.csv")
pollution['Date'] = pd.to_datetime(pollution[['Year', 'Month', 'Day']])
pollution.set_index('Date', inplace=True)
pollution = pollution[(pollution.City == 'PORT ALLEN') &
                      (pollution.index >= '2011-01-01') &
                      (pollution.index <= '2018-12-31')]
pollution = pollution.drop(['City', 'Year', 'Month', 'Day'], axis=1)

# Create a dictionary with dates and pm25 values
pm25_dict = {'Date': pd.date_range(start="2011-01-01", end="2018-12-31", freq="D"),
             'pm25': pollution['pm25'].tolist()}  # Assuming 'pm25' is the column with pm25 values

print(pm25_dict)

#Impute the missing value
# Checks for and imputes missing dates
a = pd.date_range(start="2011-01-01", end="2018-12-31", freq="D")  # Continuous dates
b = pollution.index  # Our time series
diff_dates = a.difference(b)  # Finds what in 'a' is not in 'b'

td = pd.Timedelta(1, "d")  # 1 day
for date in diff_dates:
    prev_date = date - td
    if prev_date in pollution.index:
        prev_val = pollution.loc[prev_date, 'pm25']  # Takes the previous pm25 value if it exists
        pollution.loc[date, 'pm25'] = prev_val  # Imputes previous pm25 value for the missing date

pollution.sort_index(inplace=True)
pollution.index.freq = "D"  # Sets the time index frequency as daily

print(pollution.head())

#displays a plot of the pm25 values since 2018
fig = plt.figure(figsize=(15,5))
plt.plot(pollution, color='blue')
plt.xlabel('Date')
plt.ylabel('PM 25 Value')
plt.title('Port Allen PM 25 Values 2011-2018')
plt.show()

#Split the time series data into a train and test set
end_train_ix = pd.to_datetime('2016-12-31')
train = pollution[:end_train_ix] # Jan 2011-2016
test = pollution[end_train_ix:] # Jan 2017-2018

#displays a plot of the train/test split
fig = plt.figure(figsize=(15,5))
plt.plot(train, color='purple', label='Training')
plt.plot(test, color='orange', label='Testing')
plt.xlabel('Date')
plt.ylabel('PM 2.5 Value')
plt.title('Train-Test Split')
plt.legend()
plt.show()

#Creates a windowed dataset from the time series data
WINDOW = 14 #the window value... 14 days

#converts values to TensorSliceDataset
train_data = tf.data.Dataset.from_tensor_slices(train.values)

#takes window size + 1 slices of the dataset
train_data = train_data.window(WINDOW+1, shift=1, drop_remainder=True)

#flattens windowed data by batching
train_data = train_data.flat_map(lambda x: x.batch(WINDOW+1))

#creates features and target tuple
train_data = train_data.map(lambda x: (x[:-1], x[-1]))

#shuffles dataset
train_data = train_data.shuffle(1_000)

#creates batches of windows
train_data = train_data.batch(32).prefetch(1)

from tensorflow.keras.callbacks import Callback

class CustomCallback(Callback):
    def on_epoch_end(self, epoch, logs={}):
        if logs.get('mae') < 10.0:
            print("MAE under 10.0... Stopping training")
            self.model.stop_training = True

my_callback = CustomCallback()

from tensorflow.keras.callbacks import LearningRateScheduler

#creates a function that updates the learning rate based on the epoch number
def scheduler(epoch, lr):
    if epoch < 2:
        return 0.01
    else:
        return lr * 0.99

lr_scheduler = LearningRateScheduler(scheduler)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, Lambda, Bidirectional
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import Huber


lstm_model = Sequential([
    # add extra axis to input data
    Lambda(lambda x: tf.expand_dims(x, axis=-1), input_shape=[WINDOW]),
    Bidirectional(LSTM(128, return_sequences=True)),
    Bidirectional(LSTM(128)),
    Dense(256, activation='relu'),
    Dropout(0.4),
    Dense(1)
])

lstm_model.compile(
    loss=Huber(),
    optimizer=Adam(),
    metrics=['mae']
)

lstm_model.summary()

#Trains LSTM Model
lstm_history = lstm_model.fit(
    train_data,
    epochs=100,
    callbacks=[lr_scheduler, my_callback],
    verbose=1
)

#plots training history
#Plots history of model training
plt.rcParams["figure.figsize"] = (15,5)
fig, axs = plt.subplots(1, 2)

axs[0].plot(lstm_history.history['loss'], color='red')
axs[0].set_xlabel('Epoch')
axs[0].set_ylabel('Loss')
axs[0].set_title('Training Loss')

axs[1].plot(lstm_history.history['mae'])
axs[1].set_xlabel('Epoch')
axs[1].set_ylabel('MAE')
axs[1].set_title('Training MAE')

fig.text(0.425,1, 'LSTM MODEL', {'size':25})
plt.show()

print("\t\t\t\t\tFINAL LOSS: {} | FINAL MAE: {}".format(
                                                round(lstm_history.history['loss'][-1], 2),
                                                 round(lstm_history.history['mae'][-1] ,2)))

from tensorflow.keras.layers import Conv1D, GlobalAveragePooling1D, Flatten


cnn_model = Sequential([
    # add extra axis to input data
    Lambda(lambda x: tf.expand_dims(x, axis=-1), input_shape=[WINDOW]),
    Conv1D(filters=32, kernel_size=3, strides=1,
           padding='causal', activation='relu'),
    Conv1D(filters=64, kernel_size=3, strides=1,
           padding='causal', activation='relu'),
    GlobalAveragePooling1D(),
    Flatten(),
    Dropout(0.3),
    Dense(512, activation='relu'),
    Dropout(0.4),
    Dense(1)
])

cnn_model.compile(
    loss=Huber(),
    optimizer=Adam(),
    metrics=['mae']
)

cnn_model.summary()

#Trains CNN Model
cnn_history = cnn_model.fit(
    train_data,
    epochs=100,
    callbacks=[lr_scheduler, my_callback],
    verbose=1
)

#plots training history
#Plots history of model training
plt.rcParams["figure.figsize"] = (15,5)
fig, axs = plt.subplots(1, 2)

axs[0].plot(cnn_history.history['loss'], color='red')
axs[0].set_xlabel('Epoch')
axs[0].set_ylabel('Loss')
axs[0].set_title('Training Loss')

axs[1].plot(cnn_history.history['mae'])
axs[1].set_xlabel('Epoch')
axs[1].set_ylabel('MAE')
axs[1].set_title('Training MAE')

fig.text(0.425,1, 'CNN MODEL', {'size':25})
plt.show()

print("\t\t\t\t\tFINAL LOSS: {} | FINAL MAE: {}".format(
                                                round(cnn_history.history['loss'][-1], 2),
                                                 round(cnn_history.history['mae'][-1], 2)))

mixed_model = Sequential([
    # add extra axis to input data
    Lambda(lambda x: tf.expand_dims(x, axis=-1), input_shape=[WINDOW]),
    Conv1D(filters=64, kernel_size=3, strides=1,
           padding='causal', activation='relu'),
    Bidirectional(LSTM(128, return_sequences=True)),
    Bidirectional(LSTM(128)),
    Dropout(0.3),
    Dense(512, activation='relu'),
    Dropout(0.4),
    Dense(1)
])


mixed_model.compile(
    loss=Huber(),
    optimizer=Adam(),
    metrics=['mae']
)

mixed_model.summary()

#Trains Mixed Model
mixed_history = mixed_model.fit(
    train_data,
    epochs=100,
    callbacks=[lr_scheduler, my_callback],
    verbose=1
)

#plots training history
#Plots history of model training
plt.rcParams["figure.figsize"] = (15,5)
fig, axs = plt.subplots(1, 2)

axs[0].plot(mixed_history.history['loss'], color='red')
axs[0].set_xlabel('Epoch')
axs[0].set_ylabel('Loss')
axs[0].set_title('Training Loss')

axs[1].plot(mixed_history.history['mae'])
axs[1].set_xlabel('Epoch')
axs[1].set_ylabel('MAE')
axs[1].set_title('Training MAE')

fig.text(0.425,1, 'MIXED MODEL', {'size':25})
plt.show()

print("\t\t\t\t\tFINAL LOSS: {} | FINAL MAE: {}".format(
                                                round(mixed_history.history['loss'][-1], 2),
                                                 round(mixed_history.history['mae'][-1], 2)))

import numpy as np
import pandas as pd
import tensorflow as tf

# Assuming train and test are Pandas DataFrames
# Concatenate train[-WINDOW:] and test[:-1] along rows to create forecast_data DataFrame
forecast_data = pd.concat([train[-WINDOW:], test[:-1]])

# Convert forecast_data to a NumPy array
forecast_data_array = forecast_data.values

all_models = [('LSTM MODEL', lstm_model),
              ('CNN MODEL', cnn_model),
              ('MIXED MODEL', mixed_model)]

model_forecasts = {
    'LSTM MODEL': [],
    'CNN MODEL': [],
    'MIXED MODEL': []
}

# Loop through all_models to get forecasts
for name, model in all_models:
    # Convert values to TensorSliceDataset
    test_data = tf.data.Dataset.from_tensor_slices(forecast_data_array)

    # Takes window size slices of the dataset
    test_data = test_data.window(WINDOW, shift=1, drop_remainder=True)

    # Flattens windowed data by batching
    test_data = test_data.flat_map(lambda x: x.batch(WINDOW + 1))

    # Creates batches of windows
    test_data = test_data.batch(32).prefetch(1)

    # Gets model prediction
    preds = model.predict(test_data)

    # Append to forecast dict
    model_forecasts[name].append(preds)

#Gets MAE score of model forecasts

N = test.values.shape[0] #number of samples in test set

lstm_mae = np.abs(test.values - model_forecasts['LSTM MODEL'][0].squeeze()).sum() / N

cnn_mae = np.abs(test.values - model_forecasts['CNN MODEL'][0].squeeze()).sum() / N

mix_mae = np.abs(test.values - model_forecasts['MIXED MODEL'][0].squeeze()).sum() / N


print('MODEL MAE SCORES')
print('=====================================')
print('LSTM MAE:', round(lstm_mae, 2))
print('CNN MAE:', round(cnn_mae, 2))
print('MIXED MAE:', round(mix_mae, 2))

#displays forecasted data
plt.rcParams["figure.figsize"] = (15,20)
fig, axs = plt.subplots(4, 1)

#LSTM Forecast
axs[0].plot(test.values, color='black', linestyle='--', label='Actual Value')
axs[0].plot(model_forecasts['LSTM MODEL'][0].squeeze(), color='green', label='LSTM')
axs[0].set_title('LSTM MODEL FORECAST')
axs[0].legend()

#CNN Forcast
axs[1].plot(test.values, color='black', linestyle='--', label='Actual Value')
axs[1].plot(model_forecasts['CNN MODEL'][0].squeeze(), color='blue', label='Convolution')
axs[1].set_title('CNN MODEL FORECAST')
axs[1].legend()

#Mixed Model Forecast
axs[2].plot(test.values, color='black', linestyle='--', label='Actual Value')
axs[2].plot(model_forecasts['MIXED MODEL'][0].squeeze(), color='red', label='Mixed')
axs[2].set_title('MIXED MODEL FORECAST')
axs[2].legend()

#All forecasts
axs[3].plot(test.values, color='black', linestyle='--', label='Actual Value')
axs[3].plot(model_forecasts['LSTM MODEL'][0].squeeze(), color='green', label='LSTM')
axs[3].plot(model_forecasts['CNN MODEL'][0].squeeze(), color='blue', label='Convolution')
axs[3].plot(model_forecasts['MIXED MODEL'][0].squeeze(), color='red', label='Mixed')
axs[3].set_title('ALL MODEL FORECASTS')
axs[3].legend()


plt.show()



"""#Multivariate To find the corelation about cancer, pm2.5 and copd(Final Project Implementation)"""

df = pd.read_csv('/content/PM2.5_Cancer_COPD.csv')

# Get unique values for the 'County' column
unique_counties = df['County'].unique()
print(unique_counties)

df

df.query('CancerCount!=CancerCount').count()

df.info()

df.isnull().any()

import pandas as pd
import plotly.express as px

# Assuming df is your DataFrame with columns 'CountyFIPS_Year', 'Year', 'PM2.5Value', 'CancerCount', 'COPDCount', 'TotalPopulation'

# Replace 'Suppressed', '^', and NaN with NaN in 'COPDCount' column
df['COPDCount'] = df['COPDCount'].replace(['Suppressed', '^', np.nan], pd.NA)

# Replace 'Suppressed', '^', and NaN with NaN in 'CancerCount' column
df['CancerCount'] = df['CancerCount'].replace(['^', np.nan], pd.NA)

# Convert columns to numeric
df['COPDCount'] = pd.to_numeric(df['COPDCount'], errors='coerce')
df['CancerCount'] = pd.to_numeric(df['CancerCount'], errors='coerce')

# Impute missing values in 'COPDCount' and 'CancerCount' using the mean value by Year
df['COPDCount'] = df.groupby('Year')['COPDCount'].transform(lambda x: x.fillna(x.mean()))
df['CancerCount'] = df.groupby('Year')['CancerCount'].transform(lambda x: x.fillna(x.mean()))

# Plotting PM2.5Value
pm25_fig = px.line(df, x='CountyFIPS_Year', y='PM2.5Value', color='Year', title='PM2.5Value for Each Year',hover_data=['County', 'Year'])
pm25_fig.show()

# Plotting CancerCount
cancer_fig = px.line(df, x='CountyFIPS_Year', y='CancerCount', color='Year', title='CancerCount for Each Year',hover_data=['County', 'Year'])
cancer_fig.show()

# Plotting COPDCount
copd_fig = px.line(df, x='CountyFIPS_Year', y='COPDCount', color='Year', title='COPDCount for Each Year',hover_data=['County', 'Year'])
copd_fig.show()

#!pip install plotly
import pandas as pd
import plotly.graph_objects as go

# Assuming df is your DataFrame with columns 'CountyFIPS_Year', 'Year', 'PM2.5Value', 'CancerCount', 'COPDCount', 'TotalPopulation'

# Replace 'Suppressed', '^', and NaN with NaN in 'COPDCount' column
df['COPDCount'] = df['COPDCount'].replace(['Suppressed', '^', np.nan], pd.NA)

# Replace 'Suppressed', '^', and NaN with NaN in 'CancerCount' column
df['CancerCount'] = df['CancerCount'].replace(['^', np.nan], pd.NA)

# Convert columns to numeric
df['COPDCount'] = pd.to_numeric(df['COPDCount'], errors='coerce')
df['CancerCount'] = pd.to_numeric(df['CancerCount'], errors='coerce')

# Impute missing values in 'COPDCount' and 'CancerCount' using the mean value by Year
df['COPDCount'] = df.groupby('Year')['COPDCount'].transform(lambda x: x.fillna(x.mean()))
df['CancerCount'] = df.groupby('Year')['CancerCount'].transform(lambda x: x.fillna(x.mean()))

# Filter data for each year separately
years = range(2010, 2020)  # From 2011 to 2019
data_years = [df[df['Year'] == year] for year in years]

fig = go.Figure()

for data_year in data_years:
    fig.add_trace(go.Scatter(x=data_year['CountyFIPS_Year'], y=data_year['PM2.5Value'],
                             mode='lines',
                             name=f'PM2.5Value - {data_year["Year"].unique()[0]}',
                             hovertemplate='<b>Year:</b> %{text[0]}<br>'
                                           '<b>CountyFIPS:</b> %{text[1]}<br>'
                                           '<b>PM2.5Value:</b> %{y:.2f}<extra></extra>',
                             text=data_year[['Year', 'CountyFIPS_Year']],
                             ))
    fig.add_trace(go.Scatter(x=data_year['CountyFIPS_Year'], y=data_year['CancerCount'],
                             mode='lines',
                             name=f'CancerCount - {data_year["Year"].unique()[0]}',
                             hovertemplate='<b>Year:</b> %{text[0]}<br>'
                                           '<b>CountyFIPS:</b> %{text[1]}<br>'
                                           '<b>CancerCount:</b> %{y:.2f}<extra></extra>',
                             text=data_year[['Year', 'CountyFIPS_Year']],
                             ))
    fig.add_trace(go.Scatter(x=data_year['CountyFIPS_Year'], y=data_year['COPDCount'],
                             mode='lines',
                             name=f'COPDCount - {data_year["Year"].unique()[0]}',
                             hovertemplate='<b>Year:</b> %{text[0]}<br>'
                                           '<b>CountyFIPS:</b> %{text[1]}<br>'
                                           '<b>COPDCount:</b> %{y:.2f}<extra></extra>',
                             text=data_year[['Year', 'CountyFIPS_Year']],
                             ))

fig.update_layout(title='PM2.5, Cancer, and COPD Counts for Each Year (2010-2019)',
                  xaxis_title='CountyFIPS_Year',
                  yaxis_title='Count',
                  hovermode='closest')

fig.show()

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# Replace 'Suppressed', '^', and NaN with NaN in 'COPDCount' column
df['COPDCount'] = df['COPDCount'].replace(['Suppressed', '^', np.nan], pd.NA)

# Replace 'Suppressed', '^', and NaN with NaN in 'CancerCount' column
df['CancerCount'] = df['CancerCount'].replace(['^', np.nan], pd.NA)

# Convert columns to numeric
df['COPDCount'] = pd.to_numeric(df['COPDCount'], errors='coerce')
df['CancerCount'] = pd.to_numeric(df['CancerCount'], errors='coerce')

# Impute missing values in 'COPDCount' and 'CancerCount' using the mean value by FIPS code
df['COPDCount'] = df.groupby('Year')['COPDCount'].transform(lambda x: x.fillna(x.mean()))
df['CancerCount'] = df.groupby('Year')['CancerCount'].transform(lambda x: x.fillna(x.mean()))


# Set the index inplace
df.set_index('CountyFIPS_Year', inplace=True)

# Plotting all columns (including the new columns)
df[['PM2.5Value', 'CancerCount', 'COPDCount', 'TotalPopulation']].plot(subplots=True)
plt.show()

df

"""#Multivariate for finding the corelation of other factors and pm2.5"""

# Load data from Excel file
file_path = '/content/CancerFactorsData.xlsx'
df = pd.read_excel(file_path)

#Plots all the health factors
plt.figure(figsize=(20,5))
plt.plot(df["ID"], df["PM2.5"], color='blue')
plt.plot(df["ID"], df["Smoking"], color='green')
plt.plot(df["ID"], df["Poverty"], color='red')
plt.plot(df["ID"], df["Obesity"], color='purple')
plt.plot(df["ID"], df["Uninsured"], color='orange')
plt.xlabel('Parishes_Years')
plt.xticks(rotation='vertical')
plt.ylabel('All Factors')
plt.title('Health factors for one year')
plt.show()

#Plots all the health factors based on one year
df_filtered = df[df['ID'].astype(str).str.endswith('2020')]
plt.figure(figsize=(20, 5))

# Plotting selected rows
plt.plot(df_filtered["ID"], df_filtered["PM2.5"], color='blue', label='PM2.5')
plt.plot(df_filtered["ID"], df_filtered["Smoking"], color='green', label='Smoking')
plt.plot(df_filtered["ID"], df_filtered["Poverty"], color='red', label='Poverty')
plt.plot(df_filtered["ID"], df_filtered["Obesity"], color='purple', label='Obesity')
plt.plot(df_filtered["ID"], df_filtered["Uninsured"], color='orange', label='Uninsured')

plt.xlabel('Parishes_Year')
plt.xticks(rotation='vertical')
plt.ylabel('All Factors')
plt.title('Health factors for one year')
plt.legend()
plt.show()

from sklearn.model_selection import train_test_split
# Mutlivariate Regression
# Define your input features and target variable
features = ['Smoking', 'Obesity', 'Poverty', 'Uninsured', 'PM2.5']
target = 'LungCancerRates'

# Split the data into training and testing sets
X = df[features]
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Creating Sequential model
model = Sequential()

# Adding Dense layers to create a deep neural network
model.add(Dense(64, input_shape=(len(features),), activation='relu'))  # Input layer with 64 neurons and ReLU activation
model.add(Dense(32, activation='relu'))  # Hidden layer with 32 neurons and ReLU activation
model.add(Dense(1))  # Output layer with 1 neuron (for regression task)

# Compiling the model
model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])  # Using Adam optimizer and Mean Squared Error loss

# Training the model
history = model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test), verbose=0)

# Evaluating the model
loss, mae = model.evaluate(X_test, y_test)

# Making predictions
predictions = model.predict(X_test)

# Printing sample predicted and actual values for comparison
for i in range(5):
    print(f"Predicted: {predictions[i][0]}, Actual: {y_test.iloc[i]}")

import matplotlib.pyplot as plt

# Generate indices for training and testing data points
train_indices = range(len(X_train))
test_indices = range(len(X_train), len(X_train) + len(X_test))

plt.figure(figsize=(15, 3))

# Plot training data as a line
plt.plot(train_indices, y_train, label='Training Data', color='blue')

# Plot testing data as a line
plt.plot(test_indices, y_test, label='Testing Data', color='red')

plt.xlabel('Data Points')
plt.ylabel('Lung Cancer Rates')
plt.title('Training vs. Testing Data Split')
plt.legend()
plt.show()

# Plot training and validation loss
plt.figure(figsize=(10, 6))
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training and Validation Loss')
plt.legend()
plt.show()

#Create a plot to visualize predictions vs. actuals
plt.figure(figsize=(8, 6))
plt.scatter(y_test, predictions)
plt.xlabel('Actual')
plt.ylabel('Predicted')
plt.title('Actual vs. Predicted')
plt.show()

"""#Morans'I value for pm2.5 and cancer data and interactive map"""

#!pip install pysal

#!pip install contextily

import pandas as pd
import geopandas as gpd
import folium
from pysal.explore import esda
from pysal.lib import weights
from ipywidgets import interact, IntSlider
import matplotlib.pyplot as plt
import contextily as ctx
import os
# Load the Louisiana parish boundary data
parishes_geo = gpd.read_file('/content/Louisiana_Parishes.shp')

# Specify the parishes of interest
parishes = ['Ascension', 'Caddo', 'Calcasieu', 'East Baton Rouge', 'Iberville',
            'Jefferson', 'Lafayette', 'Ouachita', 'Rapides', 'St. Bernard',
            'Tangipahoa', 'Terrebonne', 'West Baton Rouge']

# Filter the parishes_geo GeoDataFrame to include only the parishes present in the datasets
parishes_geo_filtered = parishes_geo[parishes_geo['Name'].isin(parishes)]

def create_maps(year):
    # Load the PM2.5 data for the selected year
    pm25_file = f'/content/pm2.5_{year}.csv'
    data = pd.read_csv(pm25_file)
    print(data)
    if os.path.exists(pm25_file):
      data = pd.read_csv(pm25_file)
    else:
      print(f"File not found: {pm25_file}")
    # Load the lung cancer data for the selected year
    cancer_file = f'/content/lung_cancer_{year}.csv'
    cancer_data = pd.read_csv(cancer_file)
    print(cancer_data)
    # Filter the data for the selected year and specified parishes
    data_filtered = data[(data['Year'] == year) & (data['Name'].isin(parishes))]
    cancer_data_filtered = cancer_data[(cancer_data['Year'] == year) & (cancer_data['Name'].isin(parishes))]

    # Merge the PM2.5 data with the filtered parish boundary data
    merged_data = parishes_geo_filtered.merge(data_filtered, left_on='Name', right_on='Name')

    # Merge the lung cancer data
    merged_data = merged_data.merge(cancer_data_filtered, left_on='Name', right_on='Name')

    # Calculate Moran's I for spatial autocorrelation
    w = weights.Queen.from_dataframe(merged_data)
    moran_pm25 = esda.Moran(merged_data['Mean'], w)
    moran_cancer = esda.Moran(merged_data['Rate'], w)

    # Create the non-interactive map
    fig, ax = plt.subplots(figsize=(10, 8))
    merged_data.plot(ax=ax, edgecolor='black', column='Rate', cmap='Reds', legend=True)
    merged_data.centroid.plot(ax=ax, markersize=merged_data['Mean'], color='black', alpha=0.7)
    ctx.add_basemap(ax)
    ax.set_title(f'PM2.5 Mean for Louisiana Parishes in {year}')
    ax.set_axis_off()

    # Create the interactive map centered on Louisiana
    louisiana_coords = [30.9843, -91.9623] # Coordinates for the center of Louisiana
    interactive_map = folium.Map(location=louisiana_coords, zoom_start=7)

    # Add the filtered parish polygons to the map
    folium.GeoJson(
        parishes_geo_filtered,
        name='Parishes',
        style_function=lambda feature: {
            'fillColor': 'white',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.2
        }
    ).add_to(interactive_map)

    # Add parish polygons to the map and shade them based on lung cancer rates
    folium.Choropleth(
        geo_data=merged_data,
        name='Lung Cancer Rates',
        data=merged_data,
        columns=['Name', 'Rate'],
        key_on='feature.properties.Name',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Lung Cancer Rates'
    ).add_to(interactive_map)

    # Create a feature group for PM2.5 mean values
    pm25_group = folium.FeatureGroup(name='PM2.5 Mean Values')

    # Add red circles for PM2.5 mean values
    for idx, row in merged_data.iterrows():
        folium.Circle(
            location=[row.geometry.centroid.y, row.geometry.centroid.x],
            radius=5000, # Adjust the radius as needed
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=1,
            tooltip=f"Parish: {row['Name']}<br>PM2.5 Mean: {row['Mean']:.2f}"
        ).add_to(pm25_group)

    # Add the PM2.5 feature group to the map
    pm25_group.add_to(interactive_map)

    # Add a layer control to the map
    folium.LayerControl().add_to(interactive_map)

    # Display Moran's I values
    print(f"Moran's I for PM2.5 in {year}: {moran_pm25.I:.4f}")
    print(f"Moran's I p-value for PM2.5 in {year}: {moran_pm25.p_sim:.4f}")
    print(f"Moran's I for Lung Cancer Rates in {year}: {moran_cancer.I:.4f}")
    print(f"Moran's I p-value for Lung Cancer Rates in {year}: {moran_cancer.p_sim:.4f}")

    return fig, interactive_map

# Create the interactive dashboard
@interact(year=IntSlider(min=2011, max=2020, step=1, value=2011))
def display_dashboard(year):
    fig, interactive_map = create_maps(year)
    plt.show(fig)
    display(interactive_map)

"""#Predicted PM2.5 Values for Parishes in January 2022 with LSTM(3d input and output)"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import plotly.graph_objects as go

# Load PM2.5 data
pm25_file = '/content/Monthly_PM25_Values_2011_2021.csv'
pm25_data = pd.read_csv(pm25_file)

# Split the 'Date' column into 'Year' and 'Month' columns
pm25_data[['Year', 'Month']] = pm25_data['Date'].str.split('/', expand=True)
# Check for missing values in the 'Year' column
missing_values = pm25_data['Year'].isnull().sum()
if missing_values > 0:
    print("There are missing values in the 'Year' column.")
# Drop rows with missing values in the 'Year' column
pm25_data.dropna(subset=['Year'], inplace=True)
# Recalculate last_date_year after handling missing values
last_date_index = pm25_data.index[-1]
last_date_year = int(pm25_data.loc[last_date_index, 'Year'])

# Preprocess data for LSTM
pm25_values = pm25_data['PM2.5'].values.reshape(-1, 1)  # 'PM2.5' column contains mean PM2.5 values
scaler = MinMaxScaler(feature_range=(0, 1))
pm25_scaled = scaler.fit_transform(pm25_values)
#PM2.5 Data: [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
#if time steps 3
#X = [[10, 15, 20], [15, 20, 25], [20, 25, 30], [25, 30, 35], ...]
# y = [25, 30, 35, 40, ...]

# Prepare data for LSTM (3D input)
time_steps = 10  # Define the number of time steps (adjust as needed)
X = []
y = []
for i in range(len(pm25_scaled) - time_steps):
    X.append(pm25_scaled[i:i+time_steps, 0])
    y.append(pm25_scaled[i+time_steps, 0])

X = np.array(X)
y = np.array(y)

# Reshape data for LSTM (samples, time steps, features)
X = np.reshape(X, (X.shape[0], X.shape[1], 1))

# Define and compile the LSTM model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(LSTM(units=50))
model.add(Dense(units=1))

model.compile(optimizer='adam', loss='mean_squared_error')

# Train the LSTM model
model.fit(X, y, epochs=100, batch_size=32)

# Make predictions for January 2022 (monthly predictions)
predicted_values = []
initial_sequence = X[-1]  # Initial sequence for prediction
for _ in range(1):  # Predicting for January 2022
    predicted_value = model.predict(initial_sequence.reshape(1, time_steps, 1))
    predicted_values.append(predicted_value.flatten()[0])  # Append predicted value
    initial_sequence = np.append(initial_sequence[1:], predicted_value)  # Update sequence for next prediction

# Inverse transform the predictions (if needed)
predicted_values = np.array(predicted_values).reshape(-1, 1)
predicted_values = scaler.inverse_transform(predicted_values)

# Get latitude and longitude for each parish
parish_latitudes = pm25_data['Latitude'].values
parish_longitudes = pm25_data['Longitude'].values
parish_names = pm25_data['Parish'].values  # Get parish names

# Create a Plotly scattermapbox plot for the predicted values
fig = go.Figure(go.Scattermapbox(
    lat=parish_latitudes,
    lon=parish_longitudes,
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color=predicted_values.flatten(),  # Color based on predicted PM2.5 values
        colorscale='Viridis',  # Choose a colorscale
        colorbar=dict(title='Predicted PM2.5 Values')
    ),
    text=parish_names,  # Tooltip text (Parish names)
))

fig.update_layout(
    title='Predicted PM2.5 Values for Parishes in January 2022',
    mapbox=dict(
        style='carto-positron',
        zoom=5,
        center=dict(lat=30.4583, lon=-91.1403),  # Set the center of the map
    ),
)

fig.show()

# Define and compile the LSTM model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(LSTM(units=50))
model.add(Dense(units=1))

model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])  # Add 'mae' as a monitored metric

# Train the LSTM model
history = model.fit(X, y, epochs=100, batch_size=32, validation_split=0.2)

# Get the loss and MAE history from the training
loss_history = history.history['loss']
mae_history = history.history['mae']

# Plot the training history (loss and MAE)
plt.figure(figsize=(10, 5))
plt.plot(loss_history, label='Loss', color='red')
plt.plot(mae_history, label='MAE', color='blue')
plt.xlabel('Epoch')
plt.ylabel('Metric Value')
plt.title('Training Loss and MAE')
plt.legend()
plt.show()

# Print the final loss and MAE
final_loss = loss_history[-1]
final_mae = mae_history[-1]
print(f'Final Loss: {final_loss:.4f}')
print(f'Final MAE: {final_mae:.4f}')