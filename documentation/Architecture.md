## Architecture

Elasecutor is an executor resource scheduler for data analytics systems. It predicts executors’ time-varying resource demands (step 1 in Figure 4), collects workers’ available resources (step 2), assigns executors to machines to minimize fragmentation (steps 3 and 4), elastically allocates resources (step 5), and leverages dynamic reprovisioning for better application QoS (steps 6 and 7).

![Alt text](https://github.com/NetX-lab/Elasecutor/blob/master/documentation/System_Architecture.png?raw=true "Elasecutor Architecture")

The key components are explained as follows.

### Monitor Surrogate

Elasecutor employs a monitor surrogate at each worker node to continuously monitor the resource usage of executors in real-time. It collects the process-level CPU, memory, network I/O, and disk I/O usage, and reports the time series profiles to the resource usage depository (RUD) at the master node via RPC. The information is then used to build machine learning models to predict executor resource time series. The monitor surrogate also reports the node’s future available resources to the RUD. Moreover, it monitors executor progress to see whether reprovisioning should be triggered due to significant prediction errors.

### Resource Usage Depository (RUD)

The RUD runs as a background process at the master node communicating with monitor surrogates and collecting information at each heartbeat of 3s. For simplicity we use a single master node and one RUD process, which is sufficient in our testbed evaluation. We can scale the RUD to multiple cores or multiple masters for large-scale deployment following many similar designs in distributed control plane, which is beyond the scope of this paper.

### Scheduling Module

The scheduling module decides how resources should be allocated to executors and which executors should be assigned to machines. It obtains an application’s demand time series from the prediction module. It then packs executors to machines across multiple resource types, in order to avoid overallocation and minimize fragmentation throughout the executor’s lifetime. For this purpose, we design a scheduling algorithm based on a novel metric called dominant remaining resource (DRR). Once a scheduling decision is made, the selected worker IDs along with the executor IDs are sent to Spark’s resource manager, which instructs the corresponding workers to launch the executors.

### Allocation Module

This module explicitly and dynamically sizes the resource bundles to the executor process according to the resource manager’s instructions. Through this, Elasecutor implements elastic allocation based on time-varying demands.

### Reprovisioning Module

Dynamic reprovisioning mainly deals with cases when the executor’s actual resource usage deviates significantly from the predicted time series, which is unavoidable in practice. When an executor’s progress is detected by the monitor surrogate to be slower than expected, the reprovisioning module is activated to calculate extra resources needed to make up for the slowdown.

### Prediction Module

Finally, the prediction module runs as a background process at the master node. It continuously fetches executor resource profiles from the RUD to train a prediction model for application’s resource demand time series.
