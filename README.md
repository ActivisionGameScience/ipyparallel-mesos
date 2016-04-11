# ipyparallel marathon deployment

We are heavy users of 


## Limitations

- The controller uses a large number of ports for ease of deployment the controller docker container is run in HOST networking mode. 
- Currently each engine is run under a seperate docker container. While this is great for process management the cgroup isolation disallows memmapping numpy dataframes. TODO: investigate more processes per an engine
