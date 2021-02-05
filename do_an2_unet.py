# -*- coding: utf-8 -*-
"""do_an2_unet.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AAEpVpXdETq9A3S-N5PLBvst6Fqgi9_i
"""

from google.colab import drive
drive.mount('/content/drive/')

import scipy.io as sio
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
import os,sys

test_dir='/content/drive/My Drive/Data_sunnybrook_matForm/Test'
train_dir='/content/drive/My Drive/Data_sunnybrook_matForm/Train'
val_dir='/content/drive/My Drive/Data_sunnybrook_matForm/Validation'

image_h=128
image_w=128
def load_image(dir_path):
  file_name=os.listdir(os.path.join(dir_path,'img'))
  mask_set=np.zeros((len(file_name),image_w,image_h,1))
  image_set=np.zeros((len(file_name),image_w,image_h,1))
  for i,name in enumerate(file_name):
    image_path=os.path.join(dir_path,'img',name)
    mask_path=os.path.join(dir_path,'groundtruth_endo',name)
    image=cv.resize(sio.loadmat(image_path)['img'],(image_h,image_w))
    mask=cv.resize(sio.loadmat(mask_path)['mask_endo'],(image_h,image_w))
    image_set[i,:,:,0]=image
    mask_set[i,:,:,0]=mask
    #if i%30==0:
    #  plt.subplot(1,2,1).imshow(image_set[i,:,:,0],cmap = 'gray')
    #  plt.contour(mask_set[i,:,:,0],[1],colors='green',linewidths=2)
    #  plt.draw()
    #  plt.subplot(1,2,2).imshow(mask_set[i,:,:,0],cmap = 'gray')
    #  plt.contour(mask_set[i,:,:,0],[1],colors='red',linewidths=2)
    #  plt.show()
  return image_set,mask_set

x_train,y_train=load_image(train_dir)
x_test,y_test=load_image(test_dir)
x_val,y_val=load_image(val_dir)



import tensorflow as tf 
from tensorflow import keras
from keras.preprocessing.image import ImageDataGenerator
from keras import backend as K
from keras.layers import Conv2D,Input,Conv2DTranspose,MaxPooling2D,ZeroPadding2D,Cropping2D,Concatenate,Average,Lambda,BatchNormalization,Dropout
from keras.models import Model
from keras.optimizers import SGD

def dice_coef(y_true,y_pred,smooth=1.0):
  num=2*K.sum((y_true*y_pred),axis=(1,2))
  deno=K.sum(y_true,axis=(1,2))+K.sum(y_pred,axis=(1,2))
  return num/deno
def dice_coef_loss(y_true,y_pred,smooth=1.0):
  return 1-dice_coef(y_true,y_pred)

def mvn(tensor):
    epsilon = 1e-6
    mean = K.mean(tensor, axis=(1,2), keepdims=True)
    std = K.std(tensor, axis=(1,2), keepdims=True)
    mvn = (tensor - mean) / (std + epsilon)
    
    return mvn

def U_NET(input_shape):
  input=Input(shape=input_shape,dtype=float,name='input')
  mvn1=Lambda(mvn,name='mvn_input')(input)
  conv1=Conv2D(64,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv1')(mvn1)
  mvn2=Lambda(mvn,name='mvn2')(conv1)
  conv2=Conv2D(64,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv2')(mvn2)
  mvn3=Lambda(mvn,name='mvn3')(conv2)

  pool1=MaxPooling2D(pool_size=(2,2),strides=(2,2),padding ='valid',name='pool1')(mvn3)
  conv3=Conv2D(128,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv3')(pool1)
  mvn4=Lambda(mvn,name='mvn4')(conv3)
  conv4=Conv2D(128,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv4')(mvn4)
  mvn5=Lambda(mvn,name='mvn5')(conv4)

  pool2=MaxPooling2D(pool_size=(2,2),strides=(2,2),padding='valid',name='pool2')(mvn5)
  conv5=Conv2D(256,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv5')(pool2)
  mvn6=Lambda(mvn,name='mvn6')(conv5)
  conv6=Conv2D(256,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv6')(mvn6)
  mvn7=Lambda(mvn,name='mvn7')(conv6)

  pool3=MaxPooling2D(pool_size=(2,2),strides=(2,2),padding='valid',name='pool3')(mvn7)
  conv7=Conv2D(512,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv7')(pool3)
  mvn8=Lambda(mvn,name='mvn8')(conv7)
  conv8=Conv2D(512,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv8')(mvn8)
  mvn9=Lambda(mvn,name='mvn9')(conv8)

  pool4=MaxPooling2D(pool_size=(2,2),strides=(2,2),padding='valid',name='pool4')(mvn9)
  drop1=Dropout(rate=0.5)(pool4)
  conv9=Conv2D(1024,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv9')(drop1)
  conv10=Conv2D(1024,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv10')(conv9)

  upsample1=Conv2DTranspose(512,kernel_size=(2,2),strides=(2,2),padding='valid',use_bias=False,name='upsample1')(conv10)
  merge1=Concatenate(axis=3,name='merge1')([upsample1,conv8])
  conv11=Conv2D(512,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv11')(merge1)
  conv12=Conv2D(512,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv12')(conv11)

  upsample2=Conv2DTranspose(256,kernel_size=(2,2),strides=(2,2),padding='valid',use_bias=False,name='upsample2')(conv12)
  merge2=Concatenate(axis=3,name='merge2')([upsample2,conv6])
  conv13=Conv2D(256,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv13')(merge2)
  conv14=Conv2D(256,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv14')(conv13)

  upsample3=Conv2DTranspose(128,kernel_size=(2,2),strides=(2,2),padding='valid',use_bias=False,name='upsample3')(conv14)
  merge3=Concatenate(axis=3,name='merge3')([upsample3,conv4])
  conv15=Conv2D(128,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv15')(merge3)
  conv16=Conv2D(128,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv16')(conv15)

  upsample4=Conv2DTranspose(64,kernel_size=(2,2),strides=(2,2),padding='valid',use_bias=False,name='upsample4')(conv16)
  merge4=Concatenate(axis=3,name='merge4')([upsample4,conv2])
  conv17=Conv2D(64,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv17')(merge4)
  conv18=Conv2D(64,kernel_size=(3,3),activation='relu',padding='same',use_bias=True,name='conv18')(conv17)

  predict=Conv2D(1,kernel_size=(1,1),strides=(1,1),activation='sigmoid',padding='valid',name='predict')(conv18)
  model=Model(inputs=input,outputs=predict)

  sgd = SGD(lr=0.005, momentum=0.9, nesterov=True)
  model.compile(optimizer=sgd, loss=dice_coef_loss,metrics=[dice_coef])
  #model.compile(optimizer='adam',loss='binary_crossentropy',metrics=['accuracy'])
  return model

model=U_NET(input_shape=(128,128,1))
model.summary()

class Learningrate_schedule(tf.keras.callbacks.Callback):
  def __init__(self,base_lr,max_epoch,log=None):
    self.base_lr=base_lr
    self.max_epoch=max_epoch
  def on_epoch_begin(self,epoch,log=None):
    lrate=self.base_lr*(1-epoch/self.max_epoch)**0.5
    K.set_value(model.optimizer.lr,lrate)
    print("current learning rate is:",lrate)

max_epoch=40
base_lr=model.optimizer.lr.numpy()
lrate_schedule=Learningrate_schedule(base_lr,max_epoch)
his=model.fit(x_train,y_train,batch_size=5,epochs=max_epoch,validation_data=(x_val,y_val),callbacks=lrate_schedule)

loss=his.history["loss"]
dice_coef=his.history['dice_coef']
val_loss=his.history['val_loss']
val_dice_coef=his.history['val_dice_coef']


X=np.linspace(1,max_epoch,max_epoch)
plt.figure(1)
plt.plot(X,loss,'r',label='loss')
plt.plot(X,val_loss,'b',label='val_loss')
plt.xlabel('epoch')
plt.ylabel('loss')

plt.figure(2)
plt.plot(X,dice_coef,'r',label='dice_coef')
plt.plot(X,val_dice_coef,'b',label='val_dice_coef')
plt.xlabel('epoch')
plt.ylabel('dice_coef')


plt.show()

def test(path):
  file_name=os.path.split(path)[1]
  head=os.path.split(path)[0]
  mask_path=os.path.join(os.path.split(head)[0],'groundtruth_endo',file_name)
  img=cv.resize(sio.loadmat(path)['img'],(128,128))
  mask=cv.resize(sio.loadmat(mask_path)['mask_endo'],(128,128))
  predict=model.predict(img.reshape(1,128,128,1)).reshape(128,128)
  plt.subplot(1,2,1).imshow(img,cmap='gray')
  plt.contour(predict,[0.5],colors='red',linewidth=1)
  plt.contour(mask,[0],colors='blue',linewidth=1)
  plt.draw()
  plt.subplot(1,2,2).imshow(predict,cmap='gray')
  plt.show()

for file in os.listdir('/content/drive/MyDrive/Data_sunnybrook_matForm/Test/img'):
  path=os.path.join('/content/drive/MyDrive/Data_sunnybrook_matForm/Test/img',file)
  test(path)

