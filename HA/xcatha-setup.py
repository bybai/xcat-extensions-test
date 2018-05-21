#!/usr/bin/env python
#
#  xcatha-setup.py -p <shared-data directory path> -i <nic> -v <virtual ip> [-m <netmask>] [-t <database type>] 
#

import argparse
import os
import time
import pdb

class xcat_ha_utils:

    def log_info(self, message):
        print "================================================================="
        print message

    def vip_check(self, vip):
        """check if virtual ip can ping or not"""
        self.log_info("ping virtual ip ... ...")
        pingcmd="ping -c 1 -w 10 "+vip
        res=os.system(pingcmd)
        if res is 0:
            message="Error: Aborted startup as virtual ip appears to be already active."
            self.log_info(message)
            exit(1)
        else:
            message="virtual ip can be used."
            self.log_info(message) 

    def execute_command(self, cmd):
        """"""
        loginfo="Running command:"+cmd
        print loginfo
        a=0
        while True:
            if a==3:
                loginfo=cmd+" [Failed]"
                print loginfo
                return 1
            if a >0:
                time.sleep(3)
                loginfo="Retry "+a+" ... ..."+cmd
                print loginfo
                res=os.system(cmd)
                if res is 0:
                    loginfo=cmd+" [Passed]"
                    return 0
                else:
                    a += 1

    def configure_xcat_attribute(self, host, ip):
        "configure xcat MN attribute"
        self.log_info("Configure xCAT management node attribute")
        
    def configure_vip(self, vip, nic, mask):
        """configure virtual ip"""
        self.log_info("Start configure virtual ip as alias ip")
        cmd="ifconfig "+nic+" "+vip+" "+" netmask "+mask
        res=os.system(cmd)
        if res is 0:
            message="configure virtual IP [passed]."
            self.log_info(message)
        else :
            message="Error: configure virtual IP [failed]."
            self.log_info(message) 
            exit(1)
        #add virtual ip into /etc/resolve.conf
        resolvefile=open('/etc/resolve.conf','a')
        name_server="nameserver "+vip
        resolvefile.write(name_server)
        resolvefile.close()
 
    def change_hostname(self, host, ip):
        """change hostname"""
        self.log_info("Start configure hostname")
        hostfile=open('/etc/hosts','a')
        ip_and_host=ip+" "+host
        hostfile.write(ip_and_host)
        hostfile.close()

    def unconfigure_vip(self, vip, nic):
        """remove vip from nic and /etc/resolve.conf"""
        self.log_info("remove virtual ip")
        cmd="ifconfig "+nic+" 0.0.0.0 0.0.0.0"
        print cmd
        res=os.system(cmd)
        cmd="ip addr show |grep "+vip+" &>/dev/null"
        print cmd
        res=os.system(cmd)
        if res is 0:
            message="remove virtual IP [passed]."
            self.log_info(message)
        else :
            message="Error: fail to remove virtual IP [failed]."
            self.log_info(message)
            exit(1)

    def check_service_status(service_name):
        """check service status"""
        status = os.system('systemctl status '+service_name+ ' > /dev/null')
        return status

    def finditem(n,server):
        """add item into policy table"""
        index=bytes(n)
        cmd="lsdef -t policy |grep 1."+index
        res=os.system(cmd)
        if res is not 0:
            cmd="chdef -t policy 1."+n+" name="+server+" rule=trusted"
            res=os.system(cmd)
            if res is 0:
                loginfo=cmd+" [Passed]"
                print loginfo
                return 0
            else:
                loginfo=cmd+" [Failed]"
                return 1
        else:
            n+=1
            finditem(bytes(n),server)

    def change_xcat_policy_attribute(self, nic, vip):
        """add hostname into policy table"""
        self.log_info("Configure xCAT policy table")
        filename="/etc/xcat/cert/server-cert.pem"
        word="Subject: CN="
        server=""
        with open(filename, 'r') as f:
            for l in f.readlines():
                if word in l:
                    linelist=l.split("=")
                    server=linelist[1].strip()
                    break
        if server:
            cmd="lsdef -t policy -i name|grep "+server
            res=os.system(cmd)
            if res is not 0:
                res=finditem(3,server)
                if res is 0:
                    return 0
            else:
                loginfo=server+" exist in policy table."
                return 0
        else:
            loginfo="Error: get server name "+server+" failed." 
        return 1       

    def copy_files(sourceDir, targetDir):  
        print sourceDir  
        for f in os.listdir(sourceDir):  
            sourceF = os.path.join(sourceDir, f)  
            targetF = os.path.join(targetDir, f)  
                
            if os.path.isfile(sourceF):  
                #create dir 
                if not os.path.exists(targetDir):  
                    os.makedirs(targetDir)  
              
                #if file does not exist, or size is different, overwrite
                if not os.path.exists(targetF) or (os.path.exists(targetF) and (os.path.getsize(targetF) != os.path.getsize(sourceF))):  
                    #binary
                    open(targetF, "wb").write(open(sourceF, "rb").read())  
                    print u"%s %s copy complete" %(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), targetF)  
                else:  
                    print u"%s %s existed, do not copy it" %(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), targetF)  
            if os.path.isdir(sourceF):  
                copy_files(sourceF, targetF)


    def configure_shared_data(self, path, sharedfs):
        """configure shared data directory"""
        self.log_info("configure shared data directory")
        #check if there is xcat data in shared data directory
        xcat_file_path=path+"/etc/xcat"
        if not os.path.exists(xcat_file_path):
            permision=oct(os.stat(xcat_file_path).st_mode)[-3:]           
            if permision == '755':
                i = 0
                while i < len(sharedfs):
                    xcat_file_path=path+sharedfs[i]
                    os.mkdir(xcat_file_path)
                    copy_files(sharedfs[i],xcat_file_path)
                    i += 1  
        #create symlink 
        i=0
        while i < len(sharedfs):
            print "create symlink ..."
            xcat_file_path=path+sharedfs[i]
            os.symlink(xcat_file_path, sharedfs[i]) 

def parser_arguments():
    """parser input arguments"""
    parser = argparse.ArgumentParser(description="setup and configure shared data based xCAT HA MN node")
    parser.add_argument('-p', required=True, help="shared data directory path")
    parser.add_argument('-v', required=True, help="virtual IP")
    parser.add_argument('-i', required=True, help="virtual IP network interface")
    parser.add_argument('-m', dest="netmask", default="255.255.255.0", help="virtual IP network mask")
    parser.add_argument('-n', dest="hname", help="virtual IP hostname")
    parser.add_argument('-t', dest="dbtype", default="sqlite", help="database type")
    args = parser.parse_args()
    return args

def main():
    args=parser_arguments()
    obj=xcat_ha_utils()
    obj.vip_check(args.v)

if __name__ == "__main__":
    main()
