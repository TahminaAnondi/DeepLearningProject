# Deep Learning Project README

## Table of Contents
1. [Project Overview](#project-overview)
2. [Installation Instructions](#installation-instructions)
3. [Running the Script](#running-the-script)

## Project Overview
Lung cancer is recognized as being one of the leading causes of death worldwide, and air pollution has been identified as a major contributor to its emergence. A study that was conducted in 2023 by the Journal of Thoracic Oncology revealed that air pollution was a pronounced contributor to lung cancer, with an estimated 30% increase in deaths (Berg et al., 2023). Although prior research has been conducted, there are significant gaps within the availability of data, types of data, and spatial vulnerability. 


Our study aims to bridge the gap, by examining lung cancer vulnerability parish-wide in Louisiana, we focused on identifying the most vulnerable areas and predicting the number of people that could be affected. To broaden our analysis we included additional risk factors such as, COPD, obesity, smoking, uninsured individuals, and poverty, which have conveyed to aid in an increase of developing lung cancer.


We’ve implemented several deep learning methods to predict and display the risk of lung cancer using several datasets from 2010-2021 based on Louisiana parish data. Specifically, we predicted PM2.5 values for the next 12 months in 1D utilizing Long Short-Term Memory(LSTM), Convolutional Neural Network(CNN), and mixed models. We also utilized LSTM to predict a 3D model for PM2.5 for the next month. For Spatial Correlation Analysis, we investigated the spatial correlation between lung cancer and PM2.5 values generating a map of the Louisiana parishes highlighting the comparison of the two over the span of 10 years. Moran’s I values were also calculated for each year to compare spatial autocorrelation, clustering, and variation. Lastly, a correlation and health factors impact study was conducted highlighting the correlation of COPD, and air pollution using multivariate analysis. The multivariate analysis was also utilized to analyze the impact of various health factors on lung cancer rates, aiming to understand their influence on their lung cancer incidence.


## Installation Instructions

1. Clone the GitHub repository:   
 ```python
# Code snippet
 !git clone https://github.com/TahminaAnondi/DeepLearningProject.git
```
2. Unzip the necessary files into a specific folder without creating additional subfolders:
 ```python
# Code snippet
 !unzip -j '/content/DeepLearningProject/Datasets&NecessaryFiles.zip' -d '/content/'
```
3. Change the directory to the project folder:
```python
# Code snippet
 %cd DeepLearningProject/
```

4. Install the required packages:
 ```python
# Code snippet
  !pip install pysal
  !pip install plotly
  !pip install contextily
```
## Running the script:
 ```python
# Code snippet
 %run 'predicting_the_future_risk_for_lung_cancer_in_louisiana_based_on_airpollution(pm2_5).py'
```
