#!/usr/bin/env python
#
#  xcatha-setup.py -p <shared-data directory path> -i <nic> -v <virtual ip> [-m <netmask>] [-t <database type>] 
#

import argparse
import os
import time
import platform
from subprocess import Popen, PIPE
import pdb

xcat_url="https://raw.githubusercontent.com/xcat2/xcat-core/master/xCAT-server/share/xcat/tools/go-xcat"
shared_fs=['/install','/etc/xcat','/root/.xcat','/var/lib/pgsql']

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

    def check_database_type(self, dbtype):
        """if current xcat DB type (lsxcatd -d) is different from target type, switch DB to target type"""
        self.log_info("Check database type ...")
        f=Popen(('lsxcatd', '-d'), stdout=PIPE).stdout
        data=[eachLine.strip() for eachLine in f]
        current_dbtype=filter(lambda x : 'dbengine=' in x, data)[0]
        target_dbtype="dbengine=dbtype"
        if current_dbtype != target_dbtype:
            self.switch_database(self, dbtype)

    def check_shared_data_db_type(self, dbtype, path):
        """check if target dbtype is the same with shared data dbtype"""
        self.log_info("Check if target dbtype is the same with shared data dbtype")
        cfgfile=path+"/etc/xcat/cfgloc"
        if os.path.exists(cfgfile):
            with open(r'/etc/xcat/cfgloc') as file:
                sdbtype=file.read(2)
            file.close()
            if sdbtype == 'my':
                share_data_db="mysql"
            else:
                share_data_db="postgresql"
        else:
            share_data_db="sqlite"
        print "database type is "+share_data_db+" in shared data directory"
        if share_data_db == tdbtype:
            print "target database type is matched [Passed]"
        else:
            print "Error: target database is not matched [Failed]"
            exit(1)
        
    def switch_database(self, dbtype):
        """switch database to target type"""
        res=self.install_db_package(dbtype)
        if res is 0:
            self.log_info("Switch to target database")
            if dbtype == "postgresql":
                cmd="pgsqlsetup -i -V"
                res=os.system(cmd)
                if res is 0:
                    print "Switch to "+dbtype+" [Passed]"
                else:
                    print "Switch to "+dbtype+" [Failed]"
            else:
                print "Do not support"+dbtype+" [Failed]"  

 
    def install_db_package(self, dbtype):
        """install database package"""
        self.log_info("Install database package ...")
        os_name=platform.platform()
        if os_name.__contains__("redhat") and dbtype== "postgresql":  
            cmd="yum -y install postgresql* perl-DBD-Pg"
            print "yum -y install postgresql* perl-DBD-Pg"
            res=os.system(cmd)
            if res is not 0:
                print "install postgresql* perl-DBD-Pg  package [Failed]"
            else:
                print "install postgresql* perl-DBD-Pg  package [Passed]"     
            return res

    def install_xcat(self, url):
        """install stable xCAT"""
        cmd="wget "+url+" -O - >/tmp/go-xcat"
        res=os.system(cmd)
        if res is 0:
            cmd="chmod +x /tmp/go-xcat"
            res=os.system(cmd)
            if res is 0:
                cmd="/tmp/go-xcat --yes install"
                res=os.system(cmd)
                if res is 0:
                    print "xCAT is installed [Passed]"
                    xcat_env="/opt/xcat/bin:/opt/xcat/sbin:/opt/xcat/share/xcat/tools:"
                    os.environ["PATH"]=xcat_env+os.environ["PATH"]
                    cmd="lsxcatd -v"
                    os.system(cmd)
                    return True
                else:
                    print "xCAT is installed [Failed]"
            else:
                print "chmod [Failed]"
        else:
            print "wget [Failed]"
        return False
            
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

    def check_service_status(self, service_name):
        """check service status"""
        status = os.system('systemctl status '+service_name+ ' > /dev/null')
        return status

    def finditem(self, n, server):
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

    def copy_files(self, sourceDir, targetDir):  
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
                    self.copy_files(sharedfs[i],xcat_file_path)
                    i += 1  
        #create symlink 
        i=0
        while i < len(sharedfs):
            print "create symlink ..."
            xcat_file_path=path+sharedfs[i]
            os.symlink(xcat_file_path, sharedfs[i])     
    
    def xcatha_setup_mn(self, args):
        """main process"""
        self.vip_check(args.v)
        self.check_shared_data_db_type(args.dbtype)
        self.configure_vip(args.v,args.i,args.netmask)
        self.change_hostname(args.hname,args.v)
        if self.check_service_status("xcatd") is not 0:
            install_xcat(xcat_url)
        self.check_database_type(args.dbtype)
        self.configure_shared_data(args.p, shared_fs)
        if self.check_service_status("xcatd") is not 0:
            print "Error: xCAT service does not work well [Failed]"
            exit(1)
        else:
            print "xCAT service works well [Passed]"
        self.change_xcat_policy_attribute(args.i, args.v)

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
    obj.xcatha_setup_mn(args)

if __name__ == "__main__":
    main()
