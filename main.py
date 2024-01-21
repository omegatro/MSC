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
    mapping     = elc.map_colname_colid_zotero(zotero_connection=zc, collection_name=args.c, depth=int(args.d))
    items       = elc.get_items_zotero(zc, mapping)
    pdf_url_map = elc.get_pdf_urls_zotero(items, col_name=args.c)
    
    elc.download_files(args.o, pdf_url_map)
    pdf_gen     = pp.preprocess_generator(tp.pdf_generator(args.o), output_path=os.path.join(args.o, 'wordclouds/'))
    vocab       = pp.gen_vocab(pdf_gen)
    bow_gen     = pp.bow_generator(pp.preprocess_generator(tp.pdf_generator(args.o), output_path=os.path.join(args.o, 'wordclouds/')), vocab=vocab)
    corpus      = [doc for doc in bow_gen]
    model_path  = f'./models/{args.m}.model'
    if not os.path.isfile(model_path):
        lda_model   = lda.get_lda_model(corpus=corpus, vocab=vocab, num_topics=3)
        lda_model.save(model_path)
    else:
        lda_model = lda.load_lda_model(model_path)
    lda.visualize_lda_model(model=lda_model, corpus = corpus, vocab=vocab, output_path=os.path.join(args.o,args.m))




    

if __name__ == "__main__":
    main()