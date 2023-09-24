import argparse
import sys
import logging 
import getpass
import requests
import os
import json

from concurrent.futures import ThreadPoolExecutor
from .config import BACKUP_PATH
from pyzotero import zotero

'''
Development notes

1. Parsing articles from <format> into python data structures (local storage)
2. Command-line interface
3. Connecting to external library to extract data
    https://biopython.org/docs/1.75/api/Bio.Entrez.html
    https://www.elsevier.com/solutions/sciencedirect/librarian-resource-center/api

'''

#######################
#General configurations
#######################

logging.basicConfig(level=1)


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
    def get_items_zotero(zotero_connection, colname_colid_map: dict, subset: list = None, max_workers:int=6) -> list:
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
        
        backup_check=os.path.isfile(os.path.join(BACKUP_PATH, 'pdf_url_map.json'))
        if not backup_check:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                if subset is None:
                    futures = [executor.submit(fetch_collection_items, zotero_connection, collection_id) for collection_id in colname_colid_map.values()]
                else:
                    futures = [executor.submit(fetch_collection_items, zotero_connection, colname_colid_map[n]) for n in subset if n in colname_colid_map]

            for future in futures:
                result+=future.result()

        return result


    @staticmethod
    def get_pdf_urls_zotero(items:list, backup:bool=True) -> list:
        '''
        Method to extract unique links to pdf attachments from list of zotero items
        '''
        backup_check=os.path.isfile(os.path.join(BACKUP_PATH, 'pdf_url_map.json'))
        if not backup_check:
            pdf_urls = dict()
            for item in items:
                # Check if the item has attachments
                if 'url' in item['data'] and 'pdf' in item['data']['url']:
                    if 'filename' in item['data']:
                        name = item['data']['filename']
                        if not '.pdf' in name:
                            name = name + '.pdf'
                    elif item['data']['title'] not in pdf_urls:
                        name = f"{item['data']['title']}.pdf"
                    else:
                        name = f"{item['data']['url']}.pdf"
                    pdf_urls[name] = item['data']['url']
            if backup:
                with open(os.path.join(BACKUP_PATH, 'pdf_url_map.json'), 'w+') as f:
                    json.dump(pdf_urls, f, indent=4)
        else:
            with open(os.path.join(BACKUP_PATH, 'pdf_url_map.json'), 'r+') as f:
                pdf_urls = json.load(f)
        return pdf_urls
        

    @staticmethod
    def download_files(save_path:str, name_url_dict:dict, max_workers:int=6, filters=['sciencedirect.com', 'ncbi.nlm.nih.gov']):
        '''
        Method to download files given list of urls, using requests library
        filters - databases that only allow API-based downloads
        '''
        download_counter = 0
        def dwnld_file(url, name, save_path):
            if not os.path.isfile(os.path.join(save_path, name)):
                response = requests.get(url)
                if response.status_code == 200:
                    content = response.content
                    with open(os.path.join(save_path, name), 'wb') as outfile:
                        outfile.write(content)
                    download_counter += 1
                    logging.info(f'Succesfully downloaded file\nStatus code: {response.status_code}\nURL: {url}\nName:{name}\nLocation: {save_path}')
                else:
                    logging.error(f'Failed to download file\nStatus code: {response.status_code}\nURL: {url}\nName:{name}')
            else:
                logging.info(f'Skipping download for {url} - file exists in {os.path.join(save_path, name)}')

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            [executor.submit(dwnld_file, url, name, save_path) for name, url in name_url_dict.items() if not any([f in url for f in filters])]
            logging.info(f'Succesfully downloaded {download_counter} files')
