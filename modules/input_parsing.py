import argparse
import sys
import logging 
import getpass
import requests
import os
import json
import urllib.request as libreq
import sqlite3
import shutil

from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from .config import BACKUP_PATH, host_filters
from glob import glob
from pyzotero import zotero
from PyPDF2 import PdfReader, PdfWriter, errors as pdf_errors


#######################
#General configurations
#######################

logging.basicConfig(level=1)


######################
# API access functions 
######################
            
def download_arxiv(*args, **kwargs):
    '''
    url - link to the pdf file to be downloaded
    save_path - path to the folder where the file should be saved
    name - name of the resulting pdf file

    Scope: API call wrapper for arXiv
    '''
    with libreq.urlopen(kwargs['url']) as url:
        pdf_bytes = url.read()
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with open(os.path.join(kwargs['save_path'], kwargs['name']), 'wb') as outfile:
        writer.write(outfile)


def download_ncbi_researchgate(*args, **kwargs):
    '''
    url - link to the pdf file to be downloaded
    save_path - path to the folder where the file should be saved
    name - name of the resulting pdf file

    Scope: API call wrapper for ncbi & researchgate'''
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(kwargs['url'], headers=headers)
    with open(os.path.join(kwargs['save_path'], kwargs['name']), 'wb') as outfile:
        outfile.write(response.content)


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
    @staticmethod
    def read_pdf(path, remove_corrupted=True) -> dict:
        '''
        Read text from pdf into dict of string
        mapping page numbers to its string representation.
        '''
        try:
            reader = PdfReader(path)
            num_pages = len(reader.pages)
            file = {'name': path, 'text':{i:reader.pages[i].extract_text() for i in range(num_pages)}}
            return file
        except Exception as e:
            logging.error(f'Failed to read presumed pdf file: {path} - {e}')
            if remove_corrupted:
                logging.info(f'Removing corrupted pdf file - {path}')
                os.remove(path)
            return 
    

    @staticmethod
    def pdf_generator(folder_path):
        '''Generator to parse all pdf files from folder_path'''
        pdf_list = glob(os.path.join(folder_path,'*.pdf'))
        for path in pdf_list:
            pdf = TextParser.read_pdf(path)
            if pdf is not None: yield pdf

        


#################################
#Connecting to reference managers
#################################

class LocalLibConnector():
    '''
    Toolkit class with methods for using full text copies from local Zotero storage.
    '''

    ################
    #Class variables
    ################
    
    def __init__(self,*args, **kwargs):
        '''Class variables'''
        # Local Zotero path
        user_name = os.path.basename(os.path.expanduser('~'))
        home_generic = os.path.join(os.path.expanduser('~'),'Zotero')
        pdf_names = None
        home_wsl = f'/mnt/c/Users/{user_name}/Zotero'
        if os.path.isdir(home_generic):
            self._zotero_home = home_generic
        else:
            self._zotero_home = home_wsl

    def connect_to_db(self):
        db_path = os.path.join(self._zotero_home, 'zotero.sqlite')
        if not os.path.exists(db_path):
            print("Database file not found in Zotero directory.")
            return None

        try:
            # Connect to the Zotero SQLite database
            self.conn = sqlite3.connect(db_path)
            logging.info(f'Successfully connected to {db_path}')
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            self.conn = None


    def query_local_zotero(self, collection_name:str) -> list:
        '''Sends query to local Zotero sqlite database to get file names for locally available full texts for collection and its subcollections.'''
        if self.conn is not None:
            cursor = self.conn.cursor()

            #
            query = f'''
                WITH RECURSIVE subcollections(collectionID) AS (
                SELECT collectionID FROM collections WHERE collectionName = '{collection_name}'
                UNION ALL
                SELECT c.collectionID FROM collections c JOIN subcollections sc ON c.parentCollectionID = sc.collectionID
                )
                SELECT ia.path AS attachmentKey
                FROM itemAttachments ia
                JOIN items i ON ia.parentItemID = i.itemID
                JOIN collectionItems ci ON i.itemID = ci.itemID
                WHERE ci.collectionID IN (SELECT collectionID FROM subcollections) AND ia.contentType = 'application/pdf';
            '''
            try:
                cursor.execute(query)
                items = cursor.fetchall()
                self.pdf_names = set()
                for item in items:
                    try:
                        if item[0] is not None:
                            self.pdf_names.add(item[0].replace('storage:',''))
                    except Exception as e:
                        logging.error(f'Failed to extract name from {item} - {e}')
                self.pdf_names = list(self.pdf_names)
                logging.info(f'Successfully extracted file names for {collection_name}')
                if len(self.pdf_names) == 0:
                    raise Exception(f'No documents were detected - aborting analysis - please verify that collection name was provided correctly: {collection_name}')
            except Exception as e:
                logging.error(f"Error extracting pdf names: {e}")
                sys.exit(2)
                self.pdf_names = None
            finally:
                self.conn.close()


    def get_local_copies(self, save_path:str):
        '''Copies locally-stored pdf files to save path.'''
        if self.pdf_names is None:
            print('No files to copy.')
            return
        else:
            os.makedirs(save_path, exist_ok=True)
            storage_path = os.path.join(self._zotero_home, 'storage/*/*.pdf')
            for path in glob(storage_path):
                pdf_name = os.path.basename(path)
                if pdf_name in self.pdf_names:
                    dest_path = os.path.join(save_path, pdf_name)
                    print(path, dest_path)
                    try:
                        if not os.path.isfile(dest_path):
                            shutil.copyfile(path, dest_path)
                            logging.info(f'Successful copy - {path} to {dest_path}')
                        else:
                            logging.info(f'Skipping copy - {dest_path} exists')
                    except Exception as e:
                        logging.error(f'Failed to copy {pdf_name}: {e}')
                



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
    def map_colname_colid_zotero(zotero_connection, collection_name=None, depth=-1, force_run=False):
        """
        Returns a map of collection names to collection ids with optimized fetching.

        :param zotero_connection: Pyzotero connection object.
        :param collection_name: (Optional) Name of a specific collection to map.
        :param depth: (Optional) Depth of search for subcollections.
        :return: Dictionary mapping collection names to their ids.
        """

        # Fetch all collections at once
        backup_check=os.path.isfile(os.path.join(BACKUP_PATH, f'{collection_name}.json'))
        if not backup_check or force_run:
            all_collections = zotero_connection.everything(zotero_connection.collections())
            collection_dict = {c['data']['key']: c for c in all_collections}
            parent_to_children = {c['data']['key']: [] for c in all_collections}
            for c in all_collections:
                parent_id = c['data'].get('parentCollection')
                if parent_id:
                    parent_to_children[parent_id].append(c['data']['key'])

            def map_collections(collection_id=None, current_depth=0, include_self=False):
                    if depth >= 0 and current_depth > depth:
                        return {}

                    collections_map = {}
                    if include_self and collection_id is not None:
                        # Include the current collection itself in the mapping
                        parent_collection = collection_dict[collection_id]
                        collections_map[parent_collection['data']['name']] = parent_collection['data']['key']

                    children = parent_to_children.get(collection_id, [])
                    for child_id in children:
                        child = collection_dict[child_id]
                        collections_map[child['data']['name']] = child['data']['key']
                        # Recursively map subcollections
                        collections_map.update(map_collections(child['data']['key'], current_depth + 1))

                    return collections_map

            if collection_name:
                    # Find the target collection by name
                    target_collection = next((c for c in all_collections if c['data']['name'] == collection_name), None)
                    if not target_collection:
                        raise ValueError(f"Collection named '{collection_name}' not found.")
                    return map_collections(target_collection['data']['key'], 0, include_self=True)
            else:
                # Map all collections if no specific collection name is given
                return map_collections()
        return None


    @staticmethod
    def get_items_zotero(zotero_connection, colname_colid_map: dict, max_workers:int=6) -> list:
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

        if not colname_colid_map is None:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(fetch_collection_items, zotero_connection, collection_id) for collection_id in colname_colid_map.values()]

            for future in futures:
                result+=future.result()

            return result

    @staticmethod
    def get_pdf_urls_zotero(items:list, backup:bool=True, col_name:str="pdf_url_map", force_run=False) -> list:
        '''
        Method to extract unique links to pdf attachments from list of zotero items
        '''
        backup_check=os.path.isfile(os.path.join(BACKUP_PATH, f'{col_name}.json'))
        if not backup_check or force_run:
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
                with open(os.path.join(BACKUP_PATH, f'{col_name}.json'), 'w+') as f:
                    json.dump(pdf_urls, f, indent=4)
        else:
            with open(os.path.join(BACKUP_PATH, f'{col_name}.json'), 'r+') as f:
                pdf_urls = json.load(f)
        return pdf_urls
        

    @staticmethod
    def download_files(save_path:str, name_url_dict:dict, max_workers:int=6, filters=host_filters, force_run=False):
        '''
        Method to download files given list of urls, using requests library
        filters - databases that only allow API-based downloads
        '''
        os.makedirs(save_path, exist_ok=True)
        download_counter = 0
        def dwnld_file(url, name, save_path, force_run=force_run):
            if not os.path.isfile(os.path.join(save_path, name)) or force_run:
                filter_scan = [f in url for f in filters]
                if not any(filter_scan):
                    if 'ncbi.nlm.nih.gov' in url or 'researchgate.net' in url:
                        download_ncbi_researchgate(url=url, save_path=save_path, name=name)
                    elif 'arxiv.org' in url:
                        download_arxiv(url=url, save_path=save_path, name=name)
                    else:
                        response = requests.get(url)
                        if response.status_code == 200:
                            content = response.content
                            with open(os.path.join(save_path, name), 'wb') as outfile:
                                    outfile.write(content)
                            download_counter += 1
                            logging.info(f'Succesfully downloaded file - status code: {response.status_code}\nURL: {url}\nName:{name}\nLocation: {save_path}')
                        else:
                            logging.error(f'Failed to download file - status code: {response.status_code}\nURL: {url}\nName:{name}')
                else:
                    for i, _ in enumerate(filter_scan):
                        if filter_scan[i]:
                            logging.info(f'Failed to download file - host in filter list: {url} :: {filters[i]}')
            else:
                logging.info(f'Skipping download for {url} - file exists in {os.path.join(save_path, name)}')

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            [executor.submit(dwnld_file, url, name, save_path) for name, url in name_url_dict.items()]
            logging.info(f'Succesfully downloaded {download_counter} files')





