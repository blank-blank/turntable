import sys
sys.path.append('../')

import turntable

controller = turntable.AMI_Creator()

turntable.ManagedNode(controller)

print mything