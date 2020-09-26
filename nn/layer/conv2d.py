import numpy as np
import tensorflow as tf

from typing import List, Tuple, Iterable, Union
from nn.interface import IOperator
from nn.layer.abstract import Weights, AbsLayer
from nn.activation.interface import IActivation


class Conv2DLayer(AbsLayer):

    def __init__(self, strides: Iterable[int], padding: Union[Iterable[int], str],
                 size: Iterable[int], activation: IActivation = None, inputs: IOperator = None):
        super().__init__(inputs, activation)
        self.__kernal = Weights()
        self.__strides: [List[int], Tuple[int]] = strides
        self.__padding: [List[int], Tuple[int], str] = padding
        self.__size: [List[int], Tuple[int]] = size
        self.__grad_left = None
        self.__grad_right = None
        self.__out_shape = None

    @property
    def variables(self) -> tuple:
        return self.__kernal,

    def initialize_parameters(self, x) -> None:
        if self.__kernal.get_value() is None:
            self.__kernal.set_value(np.random.uniform(low=-1, high=1, size=self.__size))

    def do_forward_predict(self, x):
        left = tf.Variable(tf.constant(x, dtype=tf.float32))
        right = tf.Variable(tf.constant(self.__kernal.get_value(), dtype=tf.float32))
        with tf.GradientTape() as tape:
            out = tf.nn.conv2d(left, right, self.__strides, self.__padding)
        self.__grad_left, self.__grad_right = tape.gradient(out, (left, right))
        self.__out_shape = out.numpy().shape
        return out.numpy()

    def do_forward_train(self, x):
        return self.do_forward_predict(x)

    def backward_adjust(self, grad) -> None:
        gw = np.multiply(self.__grad_right.numpy(), grad)
        self.__kernal.adjust(gw)

    def backward_propagate(self, grad):
        return np.multiply(self.__grad_left.numpy(), grad)

    def output_shape(self) -> [list, tuple, None]:
        return self.__out_shape

    def __str__(self):
        return "<Conv2D Layer, kernel: {}>".format(self.__size)

    def __repr__(self):
        print(self.__str__())


if __name__ == '__main__':
    import os

    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    from nn.value import Variable

    x = Variable(shape=(1, 5, 5, 1))
    y = Conv2DLayer([1, 1, 1, 1], "VALID", (2, 2, 1, 2), inputs=x)

    print(y.F())