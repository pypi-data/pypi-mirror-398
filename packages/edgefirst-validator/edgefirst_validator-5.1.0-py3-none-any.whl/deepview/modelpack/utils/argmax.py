from keras.saving import register_keras_serializable
import tensorflow as tf
import keras


@register_keras_serializable(package="deepview.modelpack.utils")
class Argmax(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, x):
        return tf.argmax(x, axis=-1, output_type=tf.int32)

    def get_config(self):
        return super().get_config()
    