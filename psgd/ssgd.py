from queue import Queue
from time import sleep

from codec.essential import BlockWeight
from psgd.interfaces import IParallelSGD


class OutdatedUpdates(Exception):

    def __init__(self):
        pass


class AsyncDetected(Exception):

    def __init__(self):
        pass


class ReadTimeOut(Exception):

    def __init__(self):
        pass


class SynchronizedSGD(IParallelSGD):
    """
        For further detail, please check class description of IParallel.
    """

    STR_BATCH_NO = 'SSGD_BATCH_NO'
    INT_READ_TIMEOUT_MS = 2000

    def __init__(self, node_id, layer_id, codec):
        """
            Initialization.
        :param node_id: the identification of current node.
        :param layer_id: the identification of working layer.
        """

        super().__init__(node_id, layer_id, codec)
        self.receive_buffer = {}
        self.batch_updater = None
        self.current_batch = 0

    def init_startup_setting(self, params=None):
        """
            Currently not used.
        :param params: None
        :return: None
        """
        pass

    def release_memory(self):
        """
            release out-dated memory for local batch buffer and codec buffer.
        """
        # remove outdated buffer
        for key in self.receive_buffer.keys():
            if key < self.current_batch - 10:
                del self.receive_buffer[key]

    def update_weights(self, content, tag):
        """
            Update weights to the cluster.
            note: only one working process on each node.
                  there can be different working progress among each nodes.
        """
        if self.batch_updater is None:
            self.batch_updater = self.Updater(tag.Node_No)

        self.current_batch = tag.Batch_No

        block = BlockWeight(tag.Layer_No, tag.Batch_No, tag.Block_No, tag.Company, content=content)

        update_pack = self.batch_updater.update_blocks(block)
        if update_pack is not None:
            sender, dic = update_pack
            dic[SynchronizedSGD.STR_BATCH_NO] = tag.Batch_No
            return sender, dic

        return None

    def accept_data(self, obj):
        """
            Accept object and put it in the queue if the data
            is way ahead of current working progress.
        """
        sender_batch = obj[SynchronizedSGD.STR_BATCH_NO]
        if sender_batch >= self.current_batch:
            self.receive_buffer[sender_batch] = self.receive_buffer.get(sender_batch, Queue())
            self.receive_buffer[sender_batch].put(obj)
        else:
            raise OutdatedUpdates()

    def require_weights(self, tag):
        """
            Synchronized weights combine.
            Decode all the data after required.
        """
        if self.current_batch != tag.Batch_No:
            raise AsyncDetected()

        time_out = 0

        while not self.batch_updater.is_done():
            # wait until more data is available
            if self.receive_buffer.get(self.current_batch) is None \
                    or self.receive_buffer[self.current_batch].empty():
                sleep(0.001)
                time_out += 1
                if time_out >= SynchronizedSGD.INT_READ_TIMEOUT_MS:
                    # read time out after INT_READ_TIMEOUT_MS million seconds
                    raise ReadTimeOut()
            if self.receive_buffer.get(self.current_batch) is not None:
                self.batch_updater.receive_blocks(self.receive_buffer[self.current_batch].get())

        if self.batch_updater.is_done():
            return self.batch_updater.get_result()
