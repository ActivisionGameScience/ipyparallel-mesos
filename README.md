# ipyparallel mesos/marathon launcher

ipyparallel has built in support for a number of backends. This is a backend for launching IPython clusters into mesos using docker and marathon.


## Quickstart

Install ipyparallel_mesos from pip or conda

pip
```
pip install ipyparallel_mesos
```

or from conda
```
# from the ActivisionGameScience conda channel
conda install --channel ActivisionGameScience ipyparallel_mesos
```

Create new ipython profile
```
ipython profile create --parallel --profile=mesos
```

Edit `~/.ipython/profile_mesos/ipcluster_config.py` and add
```
# Required
# MUST SET
c.MarathonLauncher.marathon_master_url = 'http://MARATHON_URL:8080' # url with port to a marathon master
c.MarathonLauncher.marathon_app_group = '/test/ipythontest/jdennison/' # Marathon application group. These needs to be unique per a cluster so if you have multiple users deploying clusters make sure they choose their own application group.

# Resonable defaults
c.IPClusterStart.controller_launcher_class = 'ipyparallel_mesos.launcher.MarathonControllerLauncher'
c.IPClusterEngines.engine_launcher_class = 'ipyparallel_mesos.launcher.MarathonEngineSetLauncher'

c.MarathonLauncher.controller_docker_image = 'jdennison/ipyparallel-marathon-controller:dev'  # Docker container image for the controller
c.MarathonLauncher.engine_docker_image = 'jdennison/ipyparallel-marathon-engine:dev'  # Docker image for the engine. This is where you should install custom dependencies 

# Optional
c.MarathonLauncher.engine_memory = 1024  # Amount of memory (in megabytes) to limit the docker container. NOTE: if your engine uses more the this, the docker container will be killed by the kernel without warning.
c.MarathonLauncher.controller_memory = 512  # Amount of memory (in megabytes) to limit the docker container. NOTE: if your engine uses more the this, the docker container will be killed by the kernel without warning.
c.MarathonLauncher.controller_config_port = '1235'  # The port the controller exposes for clients and engines to retrive connection information. Note, if there are multiple users on the same cluster this will need to be changed
```

While this new profile will work with the Jupyter IPython Cluter tab. You should start with the command line to help debug.
```
ipcluster start --n=4 --profile=mesos
```

As long as this command starts you should see the the docker containers in your marathon ui under the `marathon_app_group` you set earlier. You are now ready to cook with fire.

Open a new terminal session on the same machine you just ran `ipcluster`. Start Juypter or an IPython session.
```
import ipyparallel as ipp
rc = ipp.Client(profile='mesos')

import socket
rc[:].apply_async(socket.gethostname).get_dict() # Should print the hosts of the IPython engines.
```

To shut down just press Ctrl+c in the terminal you ran `ipcluster`


### Docker

ipyparallel has three main components: client, controller and engine. Please refer to the [docs](https://ipyparallel.readthedocs.org/) for a deeper dive. This project provides two docker containers to run a controller and engines in mesos cluster as well as new launchers to deploy them from ipyparallel Jupyter's cluster tab and the ipcluster cli tool. While the existing docker images are hosted publicly here for the [controller](https://hub.docker.com/r/jdennison/ipyparallel-marathon-controller/) and the [engine](https://hub.docker.com/r/jdennison/ipyparallel-marathon-engine/).

Extending the existing [ipyparallel-marathon-engine](https://hub.docker.com/r/jdennison/ipyparallel-marathon-engine/) to install your custom depencies is really useful, especially if your users have different needs. Supporting multiple version of packages for multiple users can be a real struggle. If you use a custom engine image make sure you update: `c.MarathonLauncher.engine_docker_image`.

## Design

Allowing cluster to quickly be spun up in mesos is great to help utilize existing clusters already managed by mesos. We find our workloads highly elastic so using existing resources to spin clusters up and down is very useful for us. However if you are setting up a new cluster from scratch that will be dedicated to long running IPython clusters, I would suggest using the existing SSH launcher or a for cloud based workflows something like StarCluster. Managing a mesos cluster for a single usecase might be overkill.

This package provide two launchers `MarathonControllerLauncher` and `MarathonEngineSetLauncher`. Each launcher spins up a seperate marathon applications, a single controller and N engines. The controller exposes a whole slew of ports that enable it to communicate with the engines, so this container mounts to the host's network (i.e. uses the `--net=host`) docker option. The controller writes the connection files for engines and clients and then starts a http server to expose these on the `controller_config_port`. Given the `controller_config_port` and the mesos slave that is hosting the controller you can retrieve the connection files need to connect as a client or an engine. To get these connection files, each engine container needs to know the `controller_config_port`, the controller marathon application id and the location of the marathon api in order to located the controller. If the controller was running in bridge mode, we could rely on service ports, but that is a future enhancement.

These port allocations are *not* registered to mesos which is a current limitation of the module, this could stomp on other frameworks running in your cluster. If you are deploying multiple clusters to a single mesos cluster, make sure you change the default `controller_config_port` otherwise you can get port conflicts.

## Troubleshooting

If you client doesn't have any engine registered, double check the logs in the controller and engine containers. There might be a networking issue.

## Limitations

- Have only tested against mesos v0.28.0 and marathon v0.15.0. Milage may vary on other versions.
- The entire security model of ipyparallel is to never send the key in the connection files over the network. This project completely ignores that and serves these files on an open http server. Running the engines inside containers likely offers some protection, but be warned this project make no attempt to protect you from hostile actors on your network.
- The controller uses a large number of ports, for ease of deployment the controller docker container is run in HOST networking mode. 
- Currently each engine is run under a seperate docker container. While this is great for process management the cgroup isolation disallows memmapping numpy dataframes. TODO: investigate more processes per an engine
