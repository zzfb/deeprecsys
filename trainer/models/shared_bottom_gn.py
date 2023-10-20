from typing import Dict, Text
import tensorflow as tf
import tensorflow_recommenders as tfrs
from trainer.models.common.basic_layers import MLPLayer
from trainer.models.common.multi_task import GradientNormModel

from trainer.util.tools import ObjectDict


class SharedBottomGN(GradientNormModel):
    def __init__(
        self,
        hparams: ObjectDict,
        ranking_emb: tf.keras.Model,
    ):
        super().__init__(hparams)
        self.ranking_emb = ranking_emb
        self.hparams = hparams
        self.pctr_task: tf.keras.layers.Layer = tfrs.tasks.Ranking(
            loss=tf.keras.losses.BinaryCrossentropy(),
            metrics=[tf.keras.metrics.BinaryCrossentropy(), tf.keras.metrics.AUC()],
        )
        self.pctcvr_task: tf.keras.layers.Layer = tfrs.tasks.Ranking(
            loss=tf.keras.losses.BinaryCrossentropy(),
            metrics=[tf.keras.metrics.BinaryCrossentropy(), tf.keras.metrics.AUC()],
        )
        self.shared_bottom = MLPLayer()
        # get the last dense layer, skip BN
        self.last_shared_layer = self.shared_bottom.model.get_layer(index=-2)
        self.tower1 = tf.keras.Sequential(
            [
                MLPLayer(),
                tf.keras.layers.Dense(1, "sigmoid"),
            ]
        )
        self.tower2 = tf.keras.Sequential(
            [
                MLPLayer(),
                tf.keras.layers.Dense(1, "sigmoid"),
            ]
        )

    def call(self, features: Dict[Text, tf.Tensor], training=False) -> tf.Tensor:
        shared_emb = self.ranking_emb(features, training=training)
        shared_bottom_output = self.shared_bottom(shared_emb, training=training)
        pctr = self.tower1(shared_bottom_output, training=training)
        pcvr = self.tower2(shared_bottom_output, training=training)
        return pctr, pcvr

    def compute_loss(
        self, features: Dict[Text, tf.Tensor], training=False
    ) -> tf.Tensor:
        ctr_label = tf.expand_dims(
            tf.where(features[self.hparams.label] > 0, 1, 0), axis=-1
        )
        ctcvr_label = tf.expand_dims(
            tf.where(features[self.hparams.label] > 3, 1, 0), axis=-1
        )

        pctr, pcvr = self(features, training=training)
        pctcvr = pctr * pcvr

        # pctr loss
        pctr_loss = self.pctr_task(
            labels=ctr_label,
            predictions=pctr,
            training=training,
        )
        # pctcvr loss
        pctcvr_loss = self.pctcvr_task(
            labels=ctcvr_label,
            predictions=pctcvr,
            training=training,
        )
        return [pctr_loss, pctcvr_loss]
