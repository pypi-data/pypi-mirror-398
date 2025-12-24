# ttex
Tracking Tools for (jaix) EXperiments. Published packaged on [PyPI](https://pypi.org/project/tai-ttex/)

## Wandb launching

### Prepare an executable (job)
Assuming here that launched jobs always are inside a docker image. Technically, any type of job can be used (git, code artifact or image), but this document uses image jobs as examples ([wandb_docs](https://docs.wandb.ai/guides/launch/create-launch-job)].

Create a docker image (`$image) that executes the job from an entrypoint using the launch script in this repo. A minimum version would be using the docker image produced in this repo:
```
FROM taisrc/ttex
COPY $your_code $your_code
ENTRYPOINT ["./launch.sh", "-j"]
```
An example is `taisrc/wandb:job` which is produced from this repo. Ensure that the job can be started with `./launch.sh -j`, thus it should work as:
```
python $ENTRY_PATH
```
The python script located at `$ENTRY_PATH` can access the run config as follows, and should initialise wandb:
```{python}
from wandb.sdk import launch
run_config = launch.load_wandb_config()
```


### wandb Configuration
* Set up a queue in wandb with name `$queue` ([wandb_docs](https://docs.wandb.ai/guides/launch/walkthrough#create-a-queue))
* Create a job to start your experiment. You can technically use any type of job (git, code artifact or image), To create, run the following command in an environment with wandb installed (e.g. ttex docker container)
```
wandb job create -p $project -e $entity -n $job_name -a $job_alias image $image
```


### Set up execution environment

On the environment where the jobs will be executed, we need to start a listener for new jobs.
* Clone this repository into the environment
* Set up environment file with the following variables:
```
WANDB_API_KEY=(from https://wandb.ai/authorize)
DOCKER_USER_NAME=
DOCKER_PWD=
WANDB_ENTITY=
WANDB_Q=$queue
```
* Start docker container with the listener (wandb agent)
```
docker compose up -d --remove-orphans wandb_launcher
```

### Launch a new job

Now the job can be launched from either the webpage or command line.

#### Via the webpage

Navigate to the $project page and click on "Jobs". Find the job with the selected $name and click "Launch". Launch the job with defaults or edit any of the suggested values.

#### Via the command line

:warning: This does currently not actually work, there seems to be something missing in wandb (passing the alias)

```
wandb launch -j $job_name -q $queue -e $entity -c path/to/config.json
```
