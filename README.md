# bsub_jupyter
------------

Connect to a LSF head node run a jupyter notebook via bsub and automatically open a double ssh tunnel to forward the interface on localhost.

##Dependencies

The program was tested under Linux Ubuntu 16.04 LTS and requires the following dependencies on your local machine:

* Python 2.7
* OpenSSH 5.4+

in addition, the head node of your LSF file system requires the following dependencies as well :
* Python 2.7
* OpenSSH 5.4+
* Jupyter 4.0.0+

## Installation

```
git clone https://github.com/a-slide/bsub_jupyter.git
cd bsub_jupyter
chmod u+x bsub_jupyter.py
```

Then add bsub_jupyter.py to your PATH

## Add public key to the machine

To avoid entering the password many many times to establish the connection those steps are necessary, BEFORE running the script.

Create a new ssh key if you don’t have one with the command

```
ssh-keygen
```
The key will be stored by default in: ~/.ssh/id_rsa.pub 

Install the utility ssh-copy-id if not available. 

While inside your network (or connected through the VPN) copy your public key to the main node machine with the command:

```
ssh-copy-id -i ~/.ssh/id_rsa.pub lp698@ssh.research.partners.org
```

## Usage
```
bsub_jupyter.py [-h] -U SSH_USERNAME -H SSH_HOSTNAME [-p REMOTE_PATH]   [-m MEMORY] [-t THREADS] [-q QUEUE] [-l LOCAL_PORT]  [-r REMOTE_PORT] [-v]
```

For example:
```
bsub_jupyter.py -U luke -H hh-yoda-04-01.ebi.ac.uk -p /nfs/leia/data/ -m 10000 -t 5 -q darkside -l 9999 -r 9998 --verbose
```

In verbose mode you will see:

```
    | |__  ___ _   _| |__       (_)_   _ _ __  _   _| |_ ___ _ __ 
    | '_ \/ __| | | | '_ \      | | | | | '_ \| | | | __/ _ \ '__|
    | |_) \__ \ |_| | |_) |     | | |_| | |_) | |_| | ||  __/ |   
    |_.__/|___/\__,_|_.__/____ _/ |\__,_| .__/ \__, |\__\___|_|   
                        |_____|__/      |_|    |___/             
    
    
	 username: luke
	 hostname: hh-yoda-04-01.ebi.ac.uk
	 ssh_server: luke@hh-yoda-04-01.ebi.ac.uk
	 remote_path: /nfs/leia/data/
	 memory: 10000
	 threads: 5
	 queue: darkside
	 local_port: 9999
	 remote_port: 9998
	 connection_filename: ~/jupyter_connection.txt
Host hh-yoda-04-01.ebi.ac.uk is reacheable
No running jobs were found
ssh -t luke@hh-yoda-04-01.ebi.ac.uk "bsub -e /dev/null -o /dev/null -n 5 -M 5000 -cwd /nfs/leia/data/ -q darkside jupyter notebook --port=9998 --no-browser 2>&1 >~/jupyter_connection.txt" 2> /dev/null
job running with job_id 4849293
Waiting for the job to be dispatched
. . . .

Job running on compute node: hh-yoda-02-34.ebi.ac.uk
ssh -N -L localhost:9998:localhost:9998 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o "ProxyCommand ssh luke@hh-yoda-04-01.ebi.ac.uk -W %h:%p" luke@hh-yoda-11-13.ebi.ac.uk
Tunnel created! You can see your jupyter notebook server at:

	--> http://localhost:9999 <--

Press Ctrl-c to interrupt the connection
Warning: Permanently added 'hh-yoda-11-13.ebi.ac.uk' (ECDSA) to the list of known hosts.

```

Now you can open a browser and connect to the url provided, in this case http://localhost:9999 (if not given the local and remote ports are generated at random between 9000 and 10000 to minimize conflicts with other users)

Once finished you can press Ctrl+c. The ssh tunnel and the job will be automatically killed

```
Connection interupted by user
Try to remove the connection file and kill the existing jupyter job...
Job <4849305> is being terminated
```

Options are described in the command line help:

```
bsub_jupyter.py --help
```

```
usage: bsub_jupyter.py [-h] -U SSH_USERNAME -H SSH_HOSTNAME [-p REMOTE_PATH]
                       [-m MEMORY] [-t THREADS] [-q QUEUE] [-l LOCAL_PORT]
                       [-r REMOTE_PORT] [-v]

Connect to a LSF main node directly or trough a ssh jump node launch a jupyter
notebook via bsub and open automatically a tunnel.

optional arguments:
  -h, --help            show this help message and exit
  -U SSH_USERNAME, --ssh_username SSH_USERNAME
                        Username to connect to the lsf head node [MANDATORY]
                        (default: None)
  -H SSH_HOSTNAME, --ssh_hostname SSH_HOSTNAME
                        Hostname to connect to the lsf head node [MANDATORY]
                        (default: None)
  -p REMOTE_PATH, --remote_path REMOTE_PATH
                        remote path to use (default: ~)
  -m MEMORY, --memory MEMORY
                        Memory to request (default: 5000)
  -t THREADS, --threads THREADS
                        # of threads to request (default: 1)
  -q QUEUE, --queue QUEUE
                        Queue to submit job (default: None)
  -l LOCAL_PORT, --local_port LOCAL_PORT
                        Local port for ssh forwarding (randomly generated)
                        (default: None)
  -r REMOTE_PORT, --remote_port REMOTE_PORT
                        Local port for ssh forwarding (randomly generated)
                        (default: None)
  -v, --verbose         Print debuging information (default: False)
```









