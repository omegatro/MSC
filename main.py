from modules.input_parsing import CMDInterface as cmdi, ExternalLibConnector as elc, TextParser as tp
from modules.config import argument_dict, API_KEY, LIB_ID
from modules.preprocessing import PreProcessor as pp
from modules.modeling import LatentDirichletAllocation as lda
import os
import warnings
import matplotlib
warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)


def main():
    #downloading from Zotero api and scraping available full-text pdfs
    interface   = cmdi()
    args        = interface.parse_arguments(argument_dict)
    zc          = elc.connect_zotero(library_id=LIB_ID, api_key=API_KEY, library_type='user')
    mapping     = elc.map_colname_colid_zotero(zotero_connection=zc, collection_name=args.c, depth=int(args.d), force_run=args.fa)
    items       = elc.get_items_zotero(zc, mapping)
    pdf_url_map = elc.get_pdf_urls_zotero(items, col_name=args.c, force_run=args.fa)
    
    elc.download_files(args.o, pdf_url_map)
    pdf_gen     = pp.preprocess_generator(tp.pdf_generator(args.o), output_path=os.path.join(args.o, 'wordclouds/'))
    vocab       = pp.gen_vocab(pdf_gen)
    bow_gen     = pp.bow_generator(pp.preprocess_generator(tp.pdf_generator(args.o), output_path=os.path.join(args.o, 'wordclouds/')), vocab=vocab)
    corpus      = [doc for doc in bow_gen]
    if args.mr == 'lda_gensim':
        lda.run_default_gensim_lda(
            corpus=corpus,
            vocab=vocab,
            model_path= f'./models/{args.m}_{args.mr}_{args.nt}_tpcs.model',
            num_topics = args.nt,
            visualize_lda=True,
            visual_path=os.path.join(args.o,f'{args.m}_{args.mr}_{args.nt}_tpcs')
            )

    

if __name__ == "__main__":
    main()