from modules.input_parsing import CMDInterface as cmdi, ExternalLibConnector as elc
from modules.config import argument_dict

def main():
    interface = cmdi()
    args = interface.parse_arguments(argument_dict)
    zc = elc.connect_zotero(library_id=interface.request_lib_id(), api_key=interface.request_api_key(), library_type='user')
    mapping = elc.map_colname_colid_zotero(zotero_connection=zc)
    items = elc.get_items_zotero(zc, mapping, subset=[args.l])
    

if __name__ == "__main__":
    main()