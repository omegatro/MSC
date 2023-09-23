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
                ],
                'optional':{
                    'arguments':[
                        # ['--o1','--first_optional','o1_help message', 'o1_default_value'],
                    ],
                    'flags':[
                        # ['--f1','--first_flag','f1_help message'],
                    ]
                }
            }