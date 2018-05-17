#!/usr/bin/env python
#
#  xcatha-setup.py -p <shared-data directory path> -i <nic> -v <virtual ip> [-m <netmask>] [-t <database type>] 
#

import argparse
import os
import pdb

def log_info(message):
    print "================================================================="
    print message

def parser_arguments():
    """parser input arguments"""
    parser = argparse.ArgumentParser(description="setup and configure shared data based xCAT HA MN node")
    parser.add_argument('-p', required=True, help="shared data directory path")
    parser.add_argument('-v', required=True, help="virtual IP")
    parser.add_argument('-i', required=True, help="virtual IP network interface")
    parser.add_argument('-m', dest="netmask", default="255.255.255.0", help="virtual IP network mask")
    parser.add_argument('-t', dest="dbtype", default="sqlite" help="database type")
    args = parser.parse_args()
    return args

def vip_check(vip):
    """check if virtual ip can ping or not"""
    log_info("ping virtual ip ... ...")
    pingcmd="ping -c 1 -w 10 "+vip
    res=os.system(pingcmd)
    if res is 0:
        message="Error: Aborted startup as virtual ip appears to be already active."
        log_info(message)
        exit(1)
    else :
        message="virtual ip can be used."
        log_info(message) 
        
def configure_vip(vip, nic, mask):
    """configure virtual ip"""
    log_info("Start configure virtual ip as alias ip")
    

def main():
    args=parser_arguments()
    vip_check(args.v)

if __name__ == "__main__":
    main()
