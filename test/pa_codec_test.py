import numpy as np

from codec.pacodec import PAServerCodec, PAClientComPack

from server_util.init_model import ServerUtil

from neuralnetworks.optimizer import GradientDecentOptimizer

from settings import GlobalSettings

from log import Logger


class Test_PAServer(PAServerCodec):

    def __init__(self, node_id, logger=Logger('Test')):

        PAServerCodec.__init__(node_id, logger)

        self.Working_Batch = [0 for node in GlobalSettings.getDefault().Nodes]

    def receive_blocks(self, json_dict):

        super().receive_blocks(json_dict)

        compack = PAClientComPack.decompose_compack(json_dict)
        self.Working_Batch[compack.Node_ID] += 1
        if compack.Layer_ID == 1:
            self.run_test_method(self.Current_Weights, compack.Content)

    def run_test_method(self, current_weights, content):

        x, y = ServerUtil.train_data()
        nn = ServerUtil.Neural_Network
        loss = ServerUtil.loss_type()()
        op = GradientDecentOptimizer(loss, nn)
        w = current_weights
        samples = 100
        w_1 = np.linspace(-1 + w[0, 0], 1 + w[0, 0], samples)
        w_2 = np.linspace(-1 + w[0, 1], 1 + w[0, 1], samples)
        loss_mech = np.zeros(shape=[samples, samples])

        for a in range(samples):
            for b in range(samples):
                nn[-1].W = np.asarray([w_1[a], w_2[b]]).reshape(w.shape)
                loss_mech[a][b] = op.loss(x, y)
        nn[-1].W = w
        grad = content
        scale = 1
        grad = -1 * grad * scale
        import matplotlib.pyplot as plt

        w_1, w_2 = np.meshgrid(w_1, w_2)
        fig = plt.figure()
        plt.contourf(w_1, w_2, loss_mech, levels=7)
        c = plt.contour(w_1, w_2, loss_mech, colors='black')
        plt.clabel(c, inline=True, fontsize=10)
        plt.plot([w[0, 0], w[0, 0] + grad[0, 0]], [w[0, 1], w[0, 1] + grad[0, 1]], 'r-')
        plt.plot([w[0, 0] + grad[0, 0]], [w[0, 1] + grad[0, 1]], 'r>')
        plt.savefig('./figs/bat{}.png'.format(np.max(self.Working_Batch) + 1))
        plt.close(fig)

