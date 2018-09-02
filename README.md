# Elasecutor

Elasecutor is a novel executor scheduler for data analytics systems. It dynamically allocates and explicitly sizes resources to executors over time according to the predicted time-varying resource demands. Rather than placing executors using their peak demand, Elasecutor strategically assigns them to machines based on a concept called dominant remaining resource to minimize resource fragmentation. Elasecutor further adaptively reprovisions resources in order to tolerate inaccurate demand prediction.

## Prerequisites

Spark 2.1.0, Hadoop 2.6.0, Ubuntu 16.04.2 LTS (Kernel 4.4.0), OpenJDK 7u85, cgroups management tools, psutil
Scala 2.10.4, Python 3

## Building Elasecutor

First, you need to config the environment for Spark to run and build it according to the <a href="https://github.com/apache/spark/tree/branch-2.1">documentation</a> on the project github.
Elasecutor is built using [Apache Maven](http://maven.apache.org/).
To build Elasecutor, run:

```
$ build/mvn -DskipTests clean package
```

## Basic Usage

Besides the sheduler module, Elasecutor consists of many components: Monitor Surrogate, Reprovisioning Module, Prediction Module, and Resource Usage Depository (RUD). To make them work, you need to start them manually.

You need to start Monitor Surrogate at each slave server using the following command:

```
$ python resMon.py
```

To start RUD at master server, run:
```
$ python collect.py
```
The RUD would connect to the Monitor Surrogate to get resource profiles.

Next, start Prediction Module at master servwr, run:
```
$ python predict.py
```

Finally, compile the subsystem at each slave server and correspondingly start Allocation Module.

## Workloads

We use the the workloads from <a href="https://github.com/intel-hadoop/HiBench">HiBench</a>.

## More

Please read <a href="https://github.com/NetX-lab/Elasecutor/blob/master/documentation/Architecture.md">Architecture.md</a> for more system design details.
