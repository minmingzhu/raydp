
### External Shuffle Service & Dynamic Resource Allocation

RayDP supports External Shuffle Serivce. To enable it, you can either set `spark.shuffle.service.enabled` to `true` in `spark-defaults.conf`, or you can provide a config to `raydp.init_spark`, as shown below:

```python
raydp.init_spark(..., configs={"spark.shuffle.service.enabled": "true"})
```

The user-provided config will overwrite those specified in `spark-defaults.conf`. By default Spark will load `spark-defaults.conf` from `$SPARK_HOME/conf`, you can also modify this location by setting `SPARK_CONF_DIR`.

Similarly, you can also enable Dynamic Executor Allocation this way. However, currently you must use Dynamic Executor Allocation with data persistence. You can write the data frame in spark to HDFS as a parquet as shown below:

```python
ds = RayMLDataset.from_spark(..., fs_directory="hdfs://host:port/your/directory")
```

### RayDP Executor Extra ClassPath 

As raydp starts the java executors, the classpath will contain the absolute path of ray, raydp and spark by default. When you run ray cluster on yarn([Deploying on Yarn](https://docs.ray.io/en/latest/cluster/yarn.html)), the jar files are stored on HDFS, which have different absolute path in each node. In such cases,  jvm cannot find the main class and ray workers will fail to start. 

To solve such problems, users can specify extra classpath when` init _spark` by configuring `raydp.executor.extraClassPath`. Make sure your jar files are distributed to the same path(s) on all nodes of the ray cluster.

```python
raydp.init_spark(..., configs={"raydp.executor.extraClassPath": "/your/extra/jar/path"})
```

### Spark Submit

RayDP provides a substitute for spark-submit in Apache Spark. You can run your java or scala application on RayDP cluster by using `bin/raydp-submit`. You can add it to `PATH` for convenience. When using `raydp-submit`, you should specify number of executors, number of cores and memory each executor by Spark properties, such as `--conf spark.executor.cores=1`, `--conf spark.executor.instances=1` and `--conf spark.executor.memory=500m`. `raydp-submit` only supports Ray cluster. Spark standalone, Apache Mesos, Apache Yarn are not supported, please use traditional `spark-submit` in that case. For the same reason, you do not need to specify `--master` in the command. Besides, RayDP does not support cluster as deploy-mode.