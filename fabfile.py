# -*- coding: UTF-8 -*-

from __future__ import print_function
from pprint import pprint as pp

import os
import sys
import yaml
import random

from fabric.api  import *
from fabric.state import *
from fabric.utils import *
from fabric.colors import *
from fabric.contrib import *
from fabric.decorators import *

''' read config file
'''
with open('config.yml', 'r') as cf:
    conf = yaml.safe_load(cf)

''' set environment variables
'''
env.timeout = 1
env.parallel = False
env.warn_only = True
env.forward_agent = True
env.skip_bad_hosts = True

''' set environment variables and other setting based on loaded config.yml
'''
env.user = conf['ssh_user']
env.key_filename = conf['ssh_key']

fetch_mode = conf['fetch_mode']

sentinel_key = conf['sentinel']['key']
sentinel_value = conf['sentinel']['value']

redis_key = conf['redis']['key']
redis_value = conf['redis']['value']


''' read hosts.yml file and set roles accordingly
'''
with open('hosts.yml', 'r') as hf:
    hosts = yaml.safe_load(hf)

if not hosts.has_key('sentinels'):
    print(red("ERROR: no sentinels section!"))
    sys.exit(1)
else:
    sentinel_hosts = hosts['sentinels'].split(' ')
    print("Sentinel list:", cyan(sentinel_hosts))

if not hosts.has_key('redis'):
    print(red("ERROR: no redis section!"))
    sys.exit(1)
else:
    redis_hosts = hosts['redis'].split(' ')
    print("Redis list:", cyan(redis_hosts))

def selectMaster():
    ''' pick up a random server to be our pod master
    '''
    selectMaster.master = random.choice(redis_hosts)
    global master
    return selectMaster.master
master = selectMaster()

def selectSlaves():
    ''' from redis host list, remove elected master
    '''
    global slaves
    slaves = redis_hosts[:]
    slaves.remove(master)
    return slaves
slaves = selectSlaves()

''' only set roles after electing master and define slave list
'''
env.roledefs = {
        'sentinels': sentinel_hosts,
        'redis': redis_hosts,
        'master': master,
        'slaves': slaves
    }

@roles('redis')
def runRedis(name, port):
    ''' docker run --name redis-<env> -p <port>:<port> -t -d -i redis redis-server --port <port>
    '''
    # FIXME: Test before starting container FOO on port INT if there is other container
    # already running with the same name and/or using same port
    cmd = "sudo docker run --name {name} -p {port}:{port} -t -d -i redis redis-server --port {port}".format(name=name, port=port)
    run(cmd)

def myslaves(port):
    '''
        redis-cli -h <slave_ip> -p <port> slaveof <master_ip> <port>
        redis-cli -h <slave_ip> -p <port> config set slave-read-only no
    '''
    for slave in slaves:
        print(blue("Running slaveof's"))
        print(blue(slave))
        slaveofCmd = "redis-cli -h {slave} -p {port} slaveof {master} {port}".format(slave=slave, port=port, master=master)
        local(slaveofCmd)

        print(green("Setting slave RW"))
        print(green(slave))
        roCmd = "redis-cli -h {slave} -p {port} config set slave-read-only no".format(slave=slave, port=port)
        local(roCmd)

def updateSentinels(name, port):
    '''
        redis-cli -h <sentinel_ip> -p 26379 sentinel monitor <env> <master_ip> <port> 2
        redis-cli -h <sentinel_ip> -p 26379 sentinel set <env> down-after-milliseconds 1000
        redis-cli -h <sentinel_ip> -p 26379 sentinel set <env> failover-timeout 1000
        redis-cli -h <sentinel_ip> -p 26379 sentinel set <env> parallel-syncs 1
    '''
    print(cyan("Updating sentinels"))
    for sentinel in sentinel_hosts:
        print(cyan(sentinel))
        sentinelMonitorCmd = "redis-cli -h {sentinel} -p 26379 sentinel monitor {name} {master} {port} 2".format(sentinel=sentinel, name=name, master=master, port=port)
        local(sentinelMonitorCmd)

        sentinelSetDownCmd = "redis-cli -h {sentinel} -p 26379 sentinel set {name} down-after-milliseconds 1000".format(sentinel=sentinel, name=name)
        local(sentinelSetDownCmd)

        sentinelSetFailoverCmd = "redis-cli -h {sentinel} -p 26379 sentinel set {name} failover-timeout 1000".format(sentinel=sentinel, name=name)
        local(sentinelSetFailoverCmd)

        sentinelSetParallelCmd = "redis-cli -h {sentinel} -p 26379 sentinel set {name} parallel-syncs 1".format(sentinel=sentinel, name=name)
        local(sentinelSetParallelCmd)

@task
def podName(name, port):
    ''' pick pod name to use like 'podName:redis-shoemaker,port'
    '''
    print("Pod Name:", green(name))
    print("Elected Master:", blue(master))
    print("Slave list:", cyan(slaves))

    # start redis container on all hosts
    execute(runRedis, name, port, hosts=redis_hosts)

    # start slaves
    execute(myslaves, port)

    # update sentinels
    execute(updateSentinels, name, port)

@roles('sentinels')
@task
def pingSentinels():
    ''' ping sentinels
    '''
    run('hostname')

@roles('redis')
@task
def pingRedis():
    ''' ping redis
    '''
    run('hostname')


# DONE:    define application name and port
# DONE:    run redis-<env> on every node
# DONE:    select one node to be the master of this pod
# DONE:    point all-1 instances to master (slaveof)
# DONE:    set slaves to read-only
# DONE:    add pod to sentinels (use master ip)

# TODO: use boto to fetch host dinamicaly
