
import numpy as np
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dropout, Flatten, Dense,InputLayer,Lambda
from keras.applications.resnet50 import ResNet50
from keras.models import load_model
import tensorflow.keras.backend as K
from flaskexample import app

import tensorflow as tf
import tensorflow_hub as hub

# dimensions of our images.
img_width, img_height = 640,640 #150, 150
target_width=640

#hub_to_use="https://tfhub.dev/google/imagenet/resnet_v2_50/feature_vector/1" #"https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/feature_vector/2"

top_model_weights_path = app.config['MODEL_PATH']
#top_model_weights_path='latest_model.h5'

global graph
graph = tf.get_default_graph()

#mobilenet_features_module = hub.Module(hub_to_use)
head_model=load_model(top_model_weights_path)
model_total=Sequential()
model_total.add(ResNet50(include_top=False, weights='imagenet',pooling='avg',input_shape=(target_width,target_width,3)))
#model_total.add(Lambda(mobilenet_features_module,input_shape=(target_width,target_width,3)))
model_total.add(Dense(1,activation='sigmoid'))
sess = K.get_session()
init = tf.global_variables_initializer()
sess.run(init)
model_total.layers[1].set_weights(head_model.layers[0].get_weights())
model_total.compile(optimizer='adam',
             loss='binary_crossentropy', metrics=['accuracy'])




def predict_batch(foldername):
        datagen = ImageDataGenerator(rescale=1. / 255)
        test_generator = datagen.flow_from_directory(
        foldername,
        target_size=(img_width, img_height),
        batch_size=1,
        class_mode='categorical',
        shuffle=False)
        #test_crops = crop_generator(test_generator, target_width) #RP
        N_test=len(test_generator.filenames)
        print('Starting now:',N_test)
        unpaved_ids=[]
        paved_ids=[]
        with graph.as_default():
            predictions = model_total.predict_generator(test_generator,N_test)
            for filename,prediction in zip(test_generator.filenames,predictions):
                if prediction>.5:
                    unpaved_ids.append((int(filename.split('/')[1].rstrip('.jpeg')),prediction[0]))
                    print(filename,prediction)
                else:
                    paved_ids.append((int(filename.split('/')[1].rstrip('.jpeg')),prediction[0]))
        return unpaved_ids,paved_ids



