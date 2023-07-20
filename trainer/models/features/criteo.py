from typing import Dict
import tensorflow as tf
import tensorflow_recommenders as tfrs


class CriteoDenseEmb(tfrs.Model):
    def __init__(self, meta: Dict):
        super().__init__()
        self.total_dense = 13
        self.norms = [
            tf.keras.layers.Normalization(
                mean=meta[f"dense_{i}"]["mean"], variance=meta[f"dense_{i}"]["std"]
            )
            for i in range(1, self.total_dense + 1)
        ]

    def call(self, inputs, training=False):
        return tf.concat(
            [
                self.norms[i - 1](tf.reshape(inputs[f"dense_{i}"], [-1, 1]))
                for i in range(1, self.total_dense + 1)
            ],
            axis=-1,
        )


class CriteoSparseEmb(tfrs.Model):
    def __init__(self, meta: Dict):
        super().__init__()
        self.total_sparse = 26
        self.embs = [
            tf.keras.Sequential(
                [
                    tf.keras.layers.StringLookup(
                        vocabulary=meta[f"sparse_{i}"]["vocab"]
                    ),
                    tf.keras.layers.Embedding(meta[f"sparse_{i}"]["unique"], 16),
                ]
            )
            for i in range(1, self.total_sparse + 1)
        ]

    def call(self, inputs, training=False):
        return tf.stack(
            [
                self.embs[i - 1](inputs[f"sparse_{i}"])
                for i in range(1, self.total_sparse + 1)
            ],
            axis=1,
        )
