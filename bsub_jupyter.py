#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

'''
bsub_jupyter - Luca Pinello 2016 and Adrien Leger 2017
Connect to a LSF head node, launch a jupyter notebook via bsub and open automatically a double ssh tunnel to forward the interface locally.
'''

# Standard library imports
from subprocess import call, check_output
import sys
from random import randint
import argparse
import socket
from time import sleep

# Global variables
__program__ = "bsub_jupyter"
__version__ = "0.3.0"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Main function

def bsub_jupyter():

    # Parse arguments
    try:
        parser = argparse.ArgumentParser(
            description = 'Connect to a LSF head node, launch a jupyter notebook via bsub and open automatically a double ssh tunnel to \
            forward the interface locally.',
            formatter_class = argparse.ArgumentDefaultsHelpFormatter)

        # Mandatory args
        parser.add_argument('-U', '--ssh_username', type=str, required=True, default=None,
            help='Username to connect to the lsf head node [MANDATORY]')
        parser.add_argument('-H', '--ssh_hostname', type=str, required=True, default=None,
            help='Hostname to connect to the lsf head node [MANDATORY]')

        # Optional args
        parser.add_argument('-p', '--remote_path', type=str,help='Remote path to use', default='~')
        parser.add_argument('-m', '--memory', type=int, help='Memory to request', default=5000)
        parser.add_argument('-t', '--threads', type=int, help='# of threads to request', default=1)
        parser.add_argument('-q', '--queue', type=str, help='Queue to submit job', default=None)
        parser.add_argument('-l', '--local_port', type=int, default=None,
            help='Local port for ssh forwarding (if not given will be randomly generated between 9000 and 10000)')
        parser.add_argument('-r', '--remote_port', type=int, default=None,
            help='Remote port for ssh forwarding (if not given will be randomly generated between 9000 and 10000)')
        parser.add_argument('-v', '--verbose', help='Print debugging information', default=False, action='store_true')
        parser.add_argument('-a', '--auto_add_bsub_host', default=False, action='store_true',
            help='Automatically add the compute node running the bsub jupyter job to the list of known hosts.\
            Only use this option if you are in a safe computing environment with trustworthy machines,\
            as it will also skip the host key checking')

        # Parse the args object
        args = parser.parse_args()

    except Exception:
        parser.print_help()
        sys.exit(1)

    # Save the args in local variable and verify their value if needed
    ssh_username = args.ssh_username
    ssh_hostname = args.ssh_hostname
    ssh_server = "{}@{}".format(ssh_username, ssh_hostname)
    remote_path = args.remote_path
    memory = args.memory
    threads = args.threads
    queue = args.queue
    local_port = args.local_port if args.local_port else randint(9000,10000)
    remote_port = args.remote_port if args.remote_port else randint(9000,10000)
    verbose = args.verbose
    auto_add_bsub_host = args.auto_add_bsub_host
    connection_filename= '~/jupyter_connection.txt'

    if verbose:
        print ("List of parameters:")
        print ("\t username: {}".format(ssh_username))
        print ("\t hostname: {}".format(ssh_hostname))
        print ("\t ssh_server: {}".format(ssh_server))
        print ("\t remote_path: {}".format(remote_path))
        print ("\t memory: {}".format(memory))
        print ("\t threads: {}".format(threads))
        print ("\t queue: {}".format(queue))
        print ("\t local_port: {}".format(local_port))
        print ("\t remote_port: {}".format(remote_port))
        print ("\t auto_add_bsub_host: {}".format(auto_add_bsub_host))
        print ("\t connection_filename: {}".format(connection_filename))

    # Check the host connectivity
    if verbose:
        print ('\nChecking connection status ...')

    if not hostname_resolves(ssh_hostname):
        print ('\tCannot resolve {}. Check server name and try again.'.format(ssh_hostname))
        sys.exit(1)
    if verbose:
        print ('\tHost {} is reachable'.format(ssh_hostname))

    # Check is a jupyter job is already active

    ########################################################################################################################################
    # To be removed at some point and to be replaced by a bjobs check = If jupyter found => kill it                                         #
    ########################################################################################################################################

    if ssh_file_exist (ssh_server, connection_filename):
        job_id = ssh_get_job_id (ssh_server, connection_filename)
        if verbose:
            print ('\tA connection_filename already exists with job_id {}'.format(job_id))
            print ('\tTry to remove the connection file and kill the existing jupyter job...')
        try:
            ssh_bkill_job_id (ssh_server, job_id)
            ssh_rm_file (ssh_server, connection_filename)
        except:
            pass
    else:
        if verbose:
            print ('\tNo running jobs were found')

    try:
        # Run a job jupyter notebook job
        if verbose:
            print ('\nLaunching Jupyter job ...')
        if queue:
            cmd =  """ssh -t {0} "bsub -e /dev/null -o /dev/null -n {1} -M {2} -R "rusage[mem={2}]" -cwd {3} -q {4} jupyter notebook --port={5} --no-browser 2>&1 >{6}" 2> /dev/null""".format(
                ssh_server, threads, memory, remote_path, queue, remote_port, connection_filename)
        else:
            cmd =  """ssh -t {0} "bsub -e /dev/null -o /dev/null -n {1} -M {2} -R "rusage[mem={2}]" -cwd {3} jupyter notebook --port={4} --no-browser 2>&1 >{5}" 2> /dev/null""".format(
                ssh_server, threads, memory, remote_path, remote_port, connection_filename)
        if verbose:
            print ("\tCommand line : {}".format(cmd))
        call(cmd, shell=True)

        # Fetch the job_id
        job_id = ssh_get_job_id (ssh_server, connection_filename)
        if verbose:
            print ('\tjob running with job_id {}'.format(job_id))

        # Query bjobs to get the name of the server on which jupyter is running
        print '\nWaiting for the job to be dispatched ' ,
        exec_server = None
        while exec_server is None:
            print '.',
            sys.stdout.flush()
            sleep(1)
            exec_server = ssh_get_server (ssh_server, job_id)
        print("")
        if verbose:
            print ('Job running on compute node: {}'.format(exec_server))

        # Open an ssh tunnel
        if verbose:
            print ('\nOpening a double ssh tunnel ...')
        if auto_add_bsub_host:
            cmd = 'ssh -N -L localhost:{}:localhost:{} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o "ProxyCommand ssh {} -W %h:%p" {}@{}'.format(
                local_port, remote_port, ssh_server, ssh_username, exec_server)
        else:
            cmd = 'ssh -N -L localhost:{}:localhost:{} -o "ProxyCommand ssh {} -W %h:%p" {}@{}'.format(
                local_port, remote_port, ssh_server, ssh_username, exec_server)

        if verbose:
            print ("\tCommand line : {}".format(cmd))

        print ('\nTunnel created! You can see your jupyter notebook server at:\n\n\t--> http://localhost:{} <--\n'.format(local_port))
        print ('Press Ctrl-c to interrupt the connection')
        call(cmd, shell=True)

    except KeyboardInterrupt:
        print("\nConnection interrupted by the user")

    finally:
        if verbose:
            print ('Try to remove the connection file and kill the existing jupyter job...')
        try:
            ssh_bkill_job_id (ssh_server, job_id)
            ssh_rm_file (ssh_server, connection_filename)
        except Exception:
            pass

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Helper functions

def ssh_get_job_id (ssh_server, connection_filename):
    ssh_cmd = 'ssh -t {} "head -n 1 {}" 2> /dev/null'.format(ssh_server, connection_filename)
    job_id = check_output(ssh_cmd, shell=True, universal_newlines=True).split('<')[1].split('>')[0]
    return job_id

def ssh_bkill_job_id (ssh_server, job_id):
    ssh_cmd = 'ssh -t {} "bkill {}" 2> /dev/null'.format(ssh_server, job_id)
    call(ssh_cmd, shell=True)
    return

def ssh_bjobs (ssh_server):
    ssh_cmd = 'ssh -t {} "bjobs" 2> /dev/null'.format(ssh_server)
    print (check_output(ssh_cmd, shell=True, universal_newlines=True))
    return

def ssh_rm_file (ssh_server, filename):
    ssh_cmd = 'ssh -t {} "rm {}" 2> /dev/null'.format(ssh_server, filename)
    call(ssh_cmd, shell=True)
    return

def ssh_file_exist (ssh_server, filename):
    ssh_cmd = 'ssh -q {} "[ -f {} ]" && echo "True" || echo "False"; 2> /dev/null'.format(ssh_server, filename)
    fp_exist = check_output(ssh_cmd, shell=True, universal_newlines=True).strip()
    return fp_exist == "True"

def ssh_get_server (ssh_server, job_id):
    ssh_cmd = 'ssh -t {} " bjobs -o exec_host {}" 2> /dev/null'.format(ssh_server, job_id)
    lines = check_output(ssh_cmd, shell=True, universal_newlines=True).strip()
    server = lines.strip().split("\n")[-1]
    if server == "-":
        return None
    else:
        return server.split(":")[0]

def hostname_resolves(ssh_hostname):
    try:
        socket.gethostbyname(ssh_hostname)
        return True
    except socket.error:
        return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Top level instructions

if __name__ == '__main__':
    print ('''
     _               _           _                   _
    | |__  ___ _   _| |__       (_)_   _ _ __  _   _| |_ ___ _ __
    | '_ \/ __| | | | '_ \      | | | | | '_ \| | | | __/ _ \ '__|
    | |_) \__ \ |_| | |_) |     | | |_| | |_) | |_| | ||  __/ |
    |_.__/|___/\__,_|_.__/____ _/ |\__,_| .__/ \__, |\__\___|_|
                        |_____|__/      |_|    |___/

    ''')
    bsub_jupyter()
