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
                    ['--l','--library_name','Name of the Zotero library to parse.'],
                    ['--o','--output_path','Full path to the folder where the downloaded files should be saved.'],
                ],
                'optional':{
                    'arguments':[
                        ['--mr', '--run_model', 'Name of the model to run. Currently only gensim lda supported', 'lda_gensim'],
                        ['--nt', '--num_topics', 'Number of topics to be discovered by the topic model.', 3],
                        ['--c','--collection_name','Name of the collection to parse', None],
                        ['--d','--depth','depth to go to in collection, -1 stands for full depth', -1],
                        ['--m','--model_file_name','Name of model to name the files.', 'model'],
                        ['--ng','--nram_len','Length of the n-gram', 1],
                    ],
                    'flags':[
                        ['--ul','--use_local', 'Flag to analyze locally-stored copies of publications instead of downloading from links.'],
                        ['--fa','--force_all','Flag to rerun the analysis starting from downloading the collection.'],
                        ['--sm','--skip_model','Flag to skip topic modeling'],
                        ['--wc','--word_clouds','Flag to generate wordcloud plot for each pdf file'],
                        ['--tfp','--tf_plots','Flag to generate term frequency plot for each pdf file'],
                    ]
                }
            }

#list of hosts that do not allow direct programmatic pdf downloads for open text publications
host_filters = [
    'sciencedirect.com',  
    'cell.com',
    'annualreviews.org', 
    'academic.oup.com', 
    'cancertreatmentreviews.com',
    'sciencedirectassets.com'
    ]

with open('.secrets', 'r+') as f:
    API_KEY = f.read().strip()
LIB_ID = 11755354
BACKUP_PATH = './backup'

#Preprocessing configurations
stemming_algorithm = None #'Porter' Or Snowball
extended_stopword_list = ['from', 'subject', 'edu', 'etc', 'use','https', 'http','fig','zhang', 'ner', 
                          'liu', 'lee', 'yang','ing','chen', 'authors', 'journal', 'see', 'org', 'web', 'vol', 'zhou',
                          'zhao', 'title', 'url', 'cited', 'issue', 'chang', 'page', 'tags', 'zhu', 'crossref','doi', 'nature'
                          'example', 'ncbi', 'table', 'etal']
word_cloud_plots = False
tokenizer_alg = 'nltk'
cooc_window_size = 10
