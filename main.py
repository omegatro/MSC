from modules.input_parsing import CMDInterface as cmdi, ExternalLibConnector as elc
from modules.config import argument_dict, API_KEY, LIB_ID

def main():
    interface   = cmdi()
    args        = interface.parse_arguments(argument_dict)
    zc          = elc.connect_zotero(library_id=LIB_ID, api_key=API_KEY, library_type='user')
    mapping     = elc.map_colname_colid_zotero(zotero_connection=zc)
    items       = elc.get_items_zotero(zc, mapping, subset=[args.l])
    pdf_url_map = elc.get_pdf_urls_zotero(items)
    elc.download_files(args.o, pdf_url_map)
    

if __name__ == "__main__":
    main()