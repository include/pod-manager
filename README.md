# POD-MANAGER

This simple tool uses Fabric to automate the creation of new Redis Pods running on Docker containers. It can run using a pre-defined hosts list or fetch them dynamically from AWS.

## Requirements

* Python 2.7
* Fabric

## Install

    pip install fabric

## Configure

### config.yml

* `ssh_user`: the username you are going to use to login in redis instances
* `ssh_key`: path to ssh key
* `fetch_mode`: can be `static` or `dynamic`, depending if you have a static set of hosts (sentinels and redis), or if you are going to fetch them though AWS API.
* `sentinel.key`: the AWS tag key you have defined for sentinels
* `sentinel.value`: the AWS tag value you defined for sentinels
* `redis.key`: same as above but for redis hosts
* `redis.value`: same as above but for redis hosts

### hosts.yml

Use this file if you have set `fetch_mode: static` on `config.yml`.

Something like:

    ---
    sentinels:
        172.22.41.15
        172.22.42.15
        172.22.43.15
    redis:
        172.22.41.27
        172.22.41.133
        172.22.42.122
        172.22.42.239
        172.22.43.81
        172.22.43.48

## Usage

### Task list

    fab -l

### New Pod

    fab podName:<YOURPODNAME>,<REDISPORT>,<CLUSTER>

_ie:_

    fab podName:colossus,7190,redis-cluster-2

## TODO

* Discovery using AWS API / boto
* Validations about container name and port
* define more than one cluster on `hosts.yml`
