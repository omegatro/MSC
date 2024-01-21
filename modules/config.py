'''
This is a configuration file to store constants and setups used in modules.

Expected structure:

###################
#module_name
###################

config_vars

'''

##############
#input_parsing
##############

argument_dict = {
                'description':'This is a command-line interface to interact with the MSC project.',
                'required_arguments':[
                    ['--l','--library_name','Name of the library to parse'],
                    ['--o','--output_path','Full path to the folder where the downloaded files should be saved'],
                    ['--m','--model_name','Name of model to name the model files'],
                ],
                'optional':{
                    'arguments':[
                        # ['--o1','--first_optional','o1_help message', 'o1_default_value'],
                        ['--c','--collection_name','Name of the collection to parse', None],
                        ['--d','--depth','depth to go to in collection, -1 stands for full depth', -1],
                    ],
                    'flags':[
                        # ['--f1','--first_flag','f1_help message'],
                    ]
                }
            }

#list of hosts that do not allow direct programmatic pdf downloads for open text publications
host_filters = [
    'sciencedirect.com', 
    'ncbi.nlm.nih.gov', 
    'cell.com', 
    'annualreviews.org', 
    'academic.oup.com', 
    'cancertreatmentreviews.com'
    ]

with open('.secrets', 'r+') as f:
    API_KEY = f.read().strip()
LIB_ID = 11755354
BACKUP_PATH = 'C:\\Users\\omegatro\\Desktop\\MSC\\backup'
