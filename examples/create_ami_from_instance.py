#=============================================================================
# Example of creatin ami with turntable. Create a new ami based on graylog 
# server instance.  
#=============================================================================

import datetime 
import sys
import json

#TODO: this will break on other machine
#hack sys.path to include dir with turntable
turntable_dir = "/Users/timlewis/data/dev/eclipse_workspace/turntable"
sys.path.append(turntable_dir)
import turntable

controller = turntable.DJ()

#=============================================================================

def get_managed_node_by_id(instance_id):
    '''
    params:
        instacnce_id: id of existing instance in ec2
        
    return: MangagedNode object representing 
    
    '''
    for instance in controller.get_all_instances():
        #web_id = 'i-c86a6e3f'
        #data_id = i'i-647bd0ac'
        
        if instance.id == instance_id:
            server_instance = instance
            return server_instance
       
    #if you make it out the loop, instance does not exist, so return none  
    return None

#=============================================================================

def create_new_ami(instance_id, image_name):
    '''
    create a new ami based on a running instance of graylog server, print the ami_id
    return ami_id of the newly created ami
    '''
    
    #server_id was firt, clean it if you want, just dont break it
    server_id = instance_id
   
    #TODO: image name 
    server_instance = get_managed_node_by_id(server_id)

    #during create_image(), instance will reboot, make it not delete the instance    
    disable_termination = server_instance.get_attribute('disableApiTermination')
    disable_flag = disable_termination._current_value
   
     
    if not disable_flag:
        
        server_instance.modify_attribute('disableApiTermination', True)
   
        print 'disabling accidental termination (disableApiTermination = True)'
        
        print 'creating new ami based on instance: %s: '%server_instance.id
   
   
    #add timestamp to image name 
    now_timestamp = datetime.datetime.now().strftime('%Y%m%d%_H%M')
    
    #image_name = 'working_graylog_server_%s' %now_timestamp
    image_name = '%s_%s' %(image_name, now_timestamp)

    ami_id = server_instance.create_image(image_name, description="working and configured correctly, rollback to this if trouble setting up for TR graylog arch")

        
    print 'New AMI: %s' %ami_id
   
    #change accidental termination to what it was previously 
    if not disable_flag:
        server_instance.modify_attribute('disableApiTermination', False)
   
        print 'Re-enabling accidental termination (disableApiTermination = False)'       
        
 
    return ami_id
        

#=============================================================================        


def main():

    '''
    create new graylog ami's
    '''
  
    role_dict = {'graylog_server_node':'i-8e4ee546',
                 'graylog_data_node':'i-647bd0ac',
                 'graylog_web_node':'i-c86a6e3f'}

    results = {}    
    
    for image_name, instance_id in role_dict.iteritems():
    
        print 'creating ami from %s for %s'  %(instance_id, image_name)
        role = image_name 
        
        ami_id = create_new_ami(instance_id, image_name)     

        results[role] = ami_id
        print '%s finished' %role

    
    filename = 'create_ami_from_instance.results.json'
   
     
    with open(filename, 'w') as fp:
        
        json.dump(results, fp)
#=============================================================================        


if __name__ =='__main__':

    main()