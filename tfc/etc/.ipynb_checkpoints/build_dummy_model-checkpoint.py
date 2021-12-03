import keras
import tensorflow as tf
import numpy as np

# build dummy model that just does random multiplication
# this works for the following ldmd.conf entry:
#     REQUEST UNIWISC|NIMAGE "OR_ABI-L2-CMIPPR-M6C09_G1[67].*" iddc.unidata.ucar.edu
mult = np.ones((1, 500))*0.9
input1 = tf.keras.layers.Input(shape=(500,500))
out = tf.keras.layers.multiply([input1, mult])
model = tf.keras.models.Model(inputs=input1, outputs=out)

model.save("/models/model/CMIPM1-M6C09/1")
