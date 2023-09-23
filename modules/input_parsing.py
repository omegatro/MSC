import argparse
import sys
import logging 
import getpass

from concurrent.futures import ThreadPoolExecutor
from pyzotero import zotero

'''
Development notes

1. Parsing articles from <format> into python data structures (local storage)
2. Command-line interface
3. Connecting to external library to extract data

'''

#######################
#General configurations
#######################

logging.basicConfig(level=0)


##########
#Interface
##########

class CMDInterface():
    '''
    Abstraction to store command-line arguments.
    '''
    def __init__(self) -> None:
        pass

    def parse_arguments(self, arg_dict:dict):
            """
            Parse pre-defined set of arguments from the command line, returning a namespace (object),
            that allows accessing arguments as instance variables of namespace by their full name. 
            Expected arg_dict structure:
            {
                'description':'',
                'required_arguments':[
                    ['--r1','--first_required','r1_help message'],
                    ...
                ],
                'optional':{
                    'arguments':[
                        ['--o1','--first_optional','o1_help message', 'o1_default_value'],
                        ...
                    ],
                    'flags':[
                        ['--f1','--first_flag','f1_help message'],
                        ...
                    ]
                }
            }
            """

            #Argument parsers
            parser = argparse.ArgumentParser(description=arg_dict['description'], formatter_class=argparse.RawTextHelpFormatter)
            req_arg_grp = parser.add_argument_group('Required arguments') #to display argument under required header in help message
            
            #Required
            for req_arg in arg_dict['required_arguments']: 
                req_arg_grp.add_argument(req_arg[0], req_arg[1], metavar='\b', help=req_arg[2],default=None, required=True)

            #Optional
            #Arguments
            for opt_arg in arg_dict['optional']['arguments']: 
                parser.add_argument(opt_arg[0], opt_arg[1], metavar='\b', help=opt_arg[2], default=opt_arg[3], required=False)
            
            #Flags
            for flag in arg_dict['optional']['flags']: parser.add_argument(flag[0], flag[1], help = flag[2], action='store_true')

            #If no arguments provided - display help and stop the script
            if len(sys.argv)==1: 
                parser.print_help(sys.stderr)
                sys.exit(1)
            args = parser.parse_args()
            return args
    

    @staticmethod
    def request_api_key():
        '''Requesting API key securely'''
        return getpass.getpass('Please enter your Zotero API key: ')

    
    @staticmethod
    def request_lib_id():
        '''Requesting LibraryID'''
        return input('Please enter your library id: ')


###################
#Parsing text files
###################

class TextParser():
    '''
    Toolkit class with methods for parsing different textual inputs into python data-structures.
    '''
    def __init__(self) -> None:
        pass
    

#################################
#Connecting to reference managers
#################################

class ExternalLibConnector():
    '''
    Toolkit class with methods for connecting and data retrieval from different scientific publication sources.
    '''
    def __init__(self) -> None:
        pass

    @staticmethod
    def connect_zotero(library_id, library_type, api_key):
        '''Get zotero connection object, ref. https://pyzotero.readthedocs.io/en/latest/'''
        try:
            zot = zotero.Zotero(library_id, library_type, api_key)
            logging.info(f'Successfully established connection to Zotero library: {library_id}')
            return zot
        except Exception as e:
            logging.error(f'Failed to established connection to Zotero library: {library_id}')
            logging.error(f'Exception: {e}')
    

    @staticmethod
    def map_colname_colid_zotero(zotero_connection):
        '''Returns map of collection names to collection ids, including all subcollections.'''
        col = zotero_connection.collections()
        return {c['data']['name']:c['data']['key'] for c in col}
        

    @staticmethod
    def get_items_zotero(zotero_connection, colname_colid_map: dict, subset: list = None) -> list:
        '''
        Method to extract all items from all collections in the colname_colid_map
        '''
        result = []

        def fetch_collection_items(zotero_connection, collection_id):
            '''Recursively extract items from collection and subcollection'''
            items = zotero_connection.collection_items(collection_id)
                
            # Get subcollections of the current collection
            subcollections = zotero_connection.collections_sub(collection_id)

            # Recursively fetch items from subcollections
            for subcollection in subcollections:
                subcollection_id = subcollection['key']
                subcollection_items = fetch_collection_items(zotero_connection, subcollection_id)
                items.extend(subcollection_items)

            return items

        with ThreadPoolExecutor() as executor:
            if subset is None:
                futures = [executor.submit(fetch_collection_items, zotero_connection, collection_id) for collection_id in colname_colid_map.values()]
            else:
                futures = [executor.submit(fetch_collection_items, zotero_connection, colname_colid_map[n]) for n in subset if n in colname_colid_map]

        for future in futures:
            result+=future.result()

        return result


    @staticmethod
    def get_pdfs_zotero(zotero_connection, items:list) -> list:
        '''
        Method to extract unique links to pdf attachments from list of zotero items
        '''
        pdf_urls = set()

        for item in items:
            # Check if the item has attachments
            if 'url' in item['data']:
                pdf_urls.add(item['data']['url'])
        return list(pdf_urls)
    

    @staticmethod 
    def get_html_zotero(zotero_connection, items:list) -> list:
        '''
        Method to extract unique links to html attachments from list of zotero items
        '''
        html_urls = set()

        for item in items:
            # Check if the item has attachments
            if 'url' in item['data']:
                if not 'pdf' in item['data']['url']: html_urls.add(item['data']['url'])
        return list(html_urls)