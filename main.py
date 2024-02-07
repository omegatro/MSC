from modules.input_parsing import CMDInterface as cmdi, ExternalLibConnector as elc, TextParser as tp
from modules.config import argument_dict, API_KEY, LIB_ID, stemming_algorithm, extended_stopword_list
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
    pdf_gen     = pp.preprocess_generator(tp.pdf_generator(args.o), 
                                          output_path=os.path.join(args.o, 'wordclouds/'), stemming_alg=stemming_algorithm, ext_stopword_list=extended_stopword_list)
    docs = [doc for doc in pdf_gen]
    vocab = pp.gen_vocab(docs)
    bow_gen     = pp.bow_generator(docs, vocab=vocab)
    corpus      = [bow for bow in bow_gen]
    for doc in corpus:
        for token in doc:
            if token[0] not in vocab: print(token)

    if args.mr == 'lda_gensim':
        try: 
            lda.run_default_gensim_lda(
                corpus=corpus,
                vocab=vocab,
                model_path= f'./models/{args.m}_{args.mr}_{args.nt}_tpcs.model',
                num_topics = args.nt,
                visualize_lda=True,
                visual_path=os.path.join(args.o,f'{args.m}_{args.mr}_{args.nt}_tpcs')
                )
        except IndexError:
            print('Please try to increase the number of expected topics.')

    

if __name__ == "__main__":
    main()