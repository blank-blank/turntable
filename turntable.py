#==========================================================
# This started out as graylog deploy script, but is becoming
# a one stop shop wannabe factory thing
# Things need to be separated into files
#==========================================================
import scp

import paramiko
import time
import subprocess as sp
import pprint
import json
import os
import sys
import unittest
import boto.ec2
from boto.ec2.keypair import KeyPair



import logging
logging.basicConfig(filename='turntable.log',level=logging.DEBUG)


       # #============================================================   
       # def connect_to_bastion_(bastion_uri):
       # 
       #     '''
       #     urgent and convenient
       #     return bastion host ssh connection
       #     '''
       # 
       #     #bastion_host = '52.10.194.250'
       #     key_file = '/Users/timlewis/data/dev/tpl'
       #         
       #     ssh = paramiko.SSHClient()
       #         
       #     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
       #     ssh.connect(bastion_host, username='tlewis', key_filename=key_file)
       # 
    
#============================================================
   
class BaseProvisioner(object):    
   
    '''
    Base Class for other Provisioner Classes to inherit from
    subclasses must override self.provision
    ''' 
    def provision(self):
        
        raise('You must override provision method of the BaseProvisioner Class')

#============================================================

    
class AnsibleProvisioner(BaseProvisioner):
   
    '''
    delegate object.  We'll ask the provisioner to provision
    ''' 
   
    def __init__(self, node_obj, hosts_file='hosts'): 
        self.playbook_filepath = os.path.join(os.path.dirname(__file__), 'playbook.yml')
      
        self.node_obj = node_obj
      
        self.hosts_file = hosts_file
        



    #==============================================    
    def provision(self):
    
        '''
        Calls the provisioning code specific to this provisioner
        '''       
        logging.debug('Ansible provisioner called')
        #TODO: host file is getting too many entries for public ip 
        if not self.host_exists():
            
            self.add_instance_to_hosts()
            logging.debug('adding public ip to host file')
           
        else:
            logging.debug('host exists. on to next step')
                    
                
        with open(self.hosts_file, 'a') as fp:
            

            #TODO: we need to ssh to bastion then ssh to private, instance also needs  
            fp.write(self.node_obj.ip_address + '\n')
     
        #TODO: configure these from defaults   
        pipe_obj = sp.Popen(['/usr/local/bin/ansible-playbook', '-i', self.hosts_file, self.playbook_filepath, '-vvvv', '--user', 'ubuntu' '--sudo'], stdout=sp.PIPE)
        output = pipe_obj.communicate()
      
        
        



    #============================================
    #TODO:  test this and keep fleshing out provisioners
    #============================================ 
    def host_exists(self):
        '''
        return true if this host is already in the hosts file, false otherwise
        '''

        with open(self.hosts_file, 'r') as fp:
            
            hosts_list = [host.strip() for host in fp.readlines()]
            
           
            exists = self.node_obj.ip_address in hosts_list
            
        return exists
     
    #============================================ 

    def add_instance_to_hosts(self):
    
        '''
        add public ip address of current node to the hosts file
        ''' 
        
        with open(self.hosts_file, 'a') as fp:
            print type(self.node_obj.ip_address)
            fp.write(self.node_obj.ip_address)
 
    #============================================ 





       
        
#============================================================

class ControllerTests(unittest.TestCase):
    
    def test_something(self):
        
        pass
#============================================================



provisioners_dict = {'ansible':AnsibleProvisioner}


#============================================================

class ManagedNode(object ):
    
    '''
    facade patterned class to provide handle to instance 
    '''

    #====================================
    def _install_provisioner(self, provisioner_name):
        
        try:
            provisioner_class = provisioners_dict[provisioner_name]
            provisioner_instance = provisioner_class(self)
            
            return provisioner_instance
        
        except KeyError:
            self.provisioner = None
            logging.error('No provisioner named %s' %provisioner_name)
            logging.error('Must use a correct provisioner name to continue')
            
            sys.exit(1)

    #====================================          
    def __getattribute__(self, name):
        '''
        overrides __getatribute__ to check first in managednode class.  if not 
        found, the attribute will be searched for in self.ec2_instance. If still
        not found, and exception is raised.
        '''
        try:
            return object.__getattribute__(self, name)   
        except AttributeError:
            
            try:
                return object.__getattribute__(self.ec2_instance, name)
           
            except AttributeError:
                raise
            
    #====================================       
    def __init__( self, controller, type=None, instance_obj=None, provisioner_name='ansible'):
    
        '''
       
        controller: DJ object - needs to be refactored, reworked, Just use it for now
      
        provisioner: name of a provisioner to use.  name must be in provisioners_dict dictionary 
                    and must map to a subclass of BaseProvisioner
        
        ''' 
        #lookup table where purpose is mapped to ami_id 
        self._node_types = {'graylog':'ami-f10a0fc1', 'bastion':'someami'} 

        self.type = type
        self._controller = controller
     
        self.provisioner = self._install_provisioner(provisioner_name)
     
        if type is not None: 
        #get ami_id for type if not none 
            try:
                new_ami_id = self._node_types[type]
                    
            except KeyError:
            
                #todo raise TypeNotFound Error
                print 'type not found'
                sys.exit(1)
     
        
        #ask controller 
        if instance_obj is None:
            self.ec2_instance = self._get_instance_from_controller(new_ami_id)
            
        else:
            #todo: create managednode from instance instead
            # this is not checked or even run
            self.ec2_instance = instance_obj
            
    #====================================== 
    def provision(self):
      
        logging.debug('provisioning method from ManagedNode')
        self.provisioner.provision()
        
        


    #======================================       
  
  
    def describe(self):
        return (self.ec2_instance.__dict__)
    
    
    #======================================          
    def _get_instance_from_controller(self, ami_id):

        '''
        based on ami_id, use this node's controller to create and instance
        and return that instance.
        '''        
        new_instance = self._controller.create_instance(ami_id=ami_id) 
        
        return new_instance
        
    #======================================          

    
    def run_playbook(self, playbook_uri):
       
        '''
        add instance to inventory, run a playbook from given path/url
        ''' 
        pass
    #======================================          
   
    def deploy(self):
        
        pass
    
    #======================================          

    def create_image(self):
        
        pass
    #======================================          
   
    def die(self):
        
        pass
    
    #======================================          

 
   
    
#==========================================================



class DJ(object):

    '''
    Controller class. Needs name changed.
    '''    
    def __init__(self, region='us-west-2'):
        
        self.conn = boto.ec2.connect_to_region(region)
        self.base_ami_id = 'ami-e7527ed7'
     
    
    #======================================          
      
    def get_all_instances(self, ami_id=None):
         
        reservations = self.conn.get_all_reservations()
       
                     
        instances = [i for r in reservations for i in r.instances] 
        
        if ami_id is not None:

            instances = [instance for instance in instances if instance.image_id.lower() == ami_id.lower()]
        
        return instances
   
 
    #======================================          

    def get_a_graylog_instance(self): 
        '''
        temp function to get an instance so i can instantiate and test managednode
        '''
        
        graylog_ami_id = 'ami-f10a0fc1'

        return self.get_all_instances(ami_id=graylog_ami_id)[0]
    #======================================          

    def _kill_graylog_test_instances(self):
        '''
        kill instances based on graylog ami
        '''
        #get latest id - https://github.com/Graylog2/graylog2-images/tree/master/aws 

        graylog_ami_id = 'ami-f10a0fc1'
       
         
        return self.get_all_instances(ami_id=graylog_ami_id)[0]
        
        
        
    #======================================          
       
    def get_base_ami(self):

                    
        #print self.conn.get_all_images()
        base_ami = self.conn.get_image(self.base_ami_id)
        return base_ami


    #======================================          
   
    def create_instance(self, app_name=None, ami_id=None):
        
        '''
        Create and return instance based on parameters.  app_name takes precedence.
        app_name and ami_id cannot be used together.  If neither are passed, a base
        instance is created and returned.
        The instance that is created is returned from this function.
        '''

        #lookup table for app_names and corresponding amis
        ami_dict ={'graylog':'ami-f10a0fc1',
                   'base'   : self.base_ami_id,
                   'bastion':'ami-2d6b501d' 
        } 

        
        #check that app_name and ami_id are not used at same time
        if app_name is not None and ami_id is not None:
            print 'incompatible options: app_name and ami_id cannot both be used at same time'
            sys.exit(1) 



        #app_name takes precedence over ami_id
        
        if app_name is not None:            
        
            
            try:
                ami_id = ami_dict[app_name] 
                
            except KeyError:
                
                print 'No ami id for key: %s' %app_name
                
                sys.exit(1)
                
            
       
        #if ami_id has not been set or passed, use base instance 
        if ami_id is None:
           
            ami_id = ami_dict['base']
        
        new_instance = self.conn.run_instances(ami_id, instance_type='t2.micro', key_name='main-access').instances[0]

        
        #TODO: move sleep code into green thread?  Make it more asynchronous
       
        print 'waiting for instance to become ready'   
        while new_instance.update() != 'running':
            time.sleep(5)
            
        print 'instance is ready' 
        return new_instance 


        
            
            
            
            
        
           
                    
            
#==================================================
    



def run_tests():
    print 'here'
    unittest.main()
    
#==================================================
   
    
def main():
           
   
    controller = DJ('us-west-2')
   
   
    graylog_instance = controller.create_instance(app_name='graylog')   
    mynode = ManagedNode(controller, 'graylog', instance_obj=graylog_instance, provisioner_name='ansible')    
    print mynode.ip_address
    mynode.provision() 
    #mynode.describe()



#==========================================================
#not used - clean up?
class SSH_Tunnel_Proxy_File(file):

    '''
    read and write to remote terminal from this object
    takes a client object from ssh conn
    '''

   
    def __init__(self, client_obj): 
        
        self.client_obj = client_obj
    
   
    def read(self, *args, **kwargs):
        return self.client_obj.read(self, *args, **kwargs) 
    
    def write(self, *args, **kwargs):
        return client_obj.write(self, *args, **kwargs) 
    #TODO: correct these to the three tuple returned by client_obj
        
#==========================================================    

def get_bastion_ssh_client():
    #TODO: 
    bastion_host = '52.10.194.250'
    key_file = '/Users/timlewis/data/dev/tpl'
       
    ssh_user = 'tlewis'
    client = paramiko.SSHClient()
    key_filenames=[key_file]
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    
        
    #stdin, stdout, stderr = client.exec_command('ls -l')
         
    client.connect(bastion_host, username='tlewis', key_filename=key_file)
       
    return client 
    
 #==========================================================    
  
    
    
 
def tunnel_through_bastion(command):
    
    '''
    tunnel command to new bastion
    '''   
        
          
    bastion_client = get_bastion_ssh_client()
  
    
   
    #current 
    copier = scp.SCPClient(bastion_client.get_transport())
    copier.put(__file__, '/home/tlewis/test_scp.py')
    results = bastion_client.exec_command(command)
    print results[1].read()
    return results[1].read()
    
    
    #pass the command to the ssh client
     
    
#==========================================================
    

if __name__ == '__main__':
    
    main()
    #command = 'ifconfig'
    #print tunnel_through_bastion(command)
    
    
    print 'here' 


#=======================================================
    #start instance based on base ami
    #install ansible on instance
    #download ansible playbook onto instance
    #run ansible playbook on instance
    #once configured, create new ami
    #save ami as artifact 
  
    #controller._kill_graylog_test_instances() 
    #graylog_instance = controller.get_a_graylog_instance()
 
 #=======================================================
   