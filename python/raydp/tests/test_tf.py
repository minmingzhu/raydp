#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pyspark
import pytest
import os
import sys
import shutil

import tensorflow as tf
import tensorflow.keras as keras

from pyspark.sql.functions import rand

from raydp.tf import TFEstimator
from raydp.utils import random_split

@pytest.mark.parametrize("use_fs_directory", [True, False])
def test_tf_estimator(spark_on_ray_small, use_fs_directory):
    spark = spark_on_ray_small

    # ---------------- data process with Spark ------------
    # calculate y = 3 * x + 4
    df: pyspark.sql.DataFrame = spark.range(0, 100000)
    df = df.withColumn("x", rand() * 100)  # add x column
    df = df.withColumn("y", df.x * 3 + rand() + 4)  # add y column
    df = df.select(df.x, df.y)

    train_df, test_df = random_split(df, [0.7, 0.3])

    # create model
    model = keras.Sequential(
        [
            keras.layers.InputLayer(input_shape=()),
            # Add feature dimension, expanding (batch_size,) to (batch_size, 1).
            keras.layers.Flatten(),
            keras.layers.Dense(1),
        ]
    )

    optimizer = keras.optimizers.Adam(0.01)
    loss = keras.losses.MeanSquaredError()

    estimator = TFEstimator(num_workers=2,
                            model=model,
                            optimizer=optimizer,
                            loss=loss,
                            metrics=["accuracy", "mse"],
                            feature_columns="x",
                            label_columns="y",
                            batch_size=1000,
                            num_epochs=2,
                            use_gpu=False)

    if use_fs_directory:
        dir = os.path.dirname(__file__) + "/test_tf"
        uri = "file://" + dir
        estimator.fit_on_spark(train_df, test_df, fs_directory=uri)
    else:
        estimator.fit_on_spark(train_df, test_df)
    model = estimator.get_model()
    result = model(tf.constant([0, 0]))
    assert result.shape == (2, 1)
    if use_fs_directory:
        shutil.rmtree(dir)

if __name__ == "__main__":
    # sys.exit(pytest.main(["-v", __file__]))
    import ray, raydp
    ray.init()
    spark = raydp.init_spark('a', 6, 1, '500m')
    test_tf_estimator(spark, False)
