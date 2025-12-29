import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

'''
TOPIC
'''

# redis 消息TOPIC

'''
ths 概念topic
'''

THS_CONCEPT_MSG_TOPIC = 'THS_CONCEPT_MSG_TOPIC'
'''
MSG
'''
THS_NEW_CONCEPT_ADD_MSG = 'THS_NEW_CONCEPT_ADD_MSG'

'''
自选板块股票 topic 
'''

SELF_CHOOSE_TOPIC = 'SELF_CHOOSE_TOPIC'
'''
MSG
'''
SELF_CHOOSE_CHANGE_MSG = 'SELF_CHOOSE_CHANGE_MSG'
