# -*- coding: utf-8 -*-
"""TimeSeries-hydrogeneration.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zsxYV3oSpreareA00m97K5gLa0W-nuA1
"""

import os
os.environ['KAGGLE_USERNAME'] = #'user'
os.environ['KAGGLE_KEY'] = #'key'

!kaggle datasets download -d navinmundhra/daily-power-generation-in-india-20172020

!unzip -q daily-power-generation-in-india-20172020 -d .

import numpy as np
import pandas as pd
from keras.layers import Dense, LSTM
import matplotlib.pyplot as plt
import tensorflow as tf

df = pd.read_csv('file_02.csv')
df.info()

df = df[df.Region == 'Eastern']
df.head()

df.info()

df.isnull().sum()

dates = df['Date'].values
rates = df['Hydro Generation Actual (in MU)'].values
rates = rates.astype(float)
 
plt.figure(figsize=(15,5))
plt.plot(dates, rates)
plt.title('Minimal Temperature of Seattle',
          fontsize=20);

#mae acuan
mae10 = (max(rates) - min(rates))*0.1
mae10

#splitting training and test set
x_train = dates[:int(dates.shape[0]*0.8)]
x_test = dates[int(dates.shape[0]*0.8):]
y_train = rates[:int(dates.shape[0]*0.8)]
y_test = rates[int(dates.shape[0]*0.8):]

#defining window function
def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

#assign test and train set
train_set = windowed_dataset(y_train, window_size=60, batch_size=100, shuffle_buffer=1000)
test_set = windowed_dataset(y_test, window_size=60, batch_size=100, shuffle_buffer=1000)

#create sequential model
model = tf.keras.models.Sequential([
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.LSTM(64),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(32, activation="relu"),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(64, activation="relu"),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(128, activation="relu"),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(256, activation="relu"),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(512, activation="relu"),
  tf.keras.layers.Dense(1)
])

#compile
optimizer = tf.keras.optimizers.SGD(lr=1.0000e-04, momentum=0.9)

model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

#callback function
class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('val_mae')<mae10 and logs.get('mae')<mae10):
      print("\nMAE telah mencapai < 10% skala data!")
      self.model.stop_training = True
callbacks = myCallback()

#train data
history = model.fit(train_set,
                    validation_data=test_set,
                    epochs=200,
                    callbacks=[callbacks])