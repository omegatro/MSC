import os
import warnings
import matplotlib

from modules.input_parsing import CMDInterface as cmdi, ExternalLibConnector as elc, LocalLibConnector as llc, TextParser as tp
from modules.config import argument_dict, API_KEY, LIB_ID, stemming_algorithm, extended_stopword_list, tokenizer_alg, cooc_window_size, upper_freq_th, lower_freq_th
from modules.preprocessing import PreProcessor as pp
from modules.modeling import LatentDirichletAllocation as lda
warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pyLDAvis.*")


def main():
    '''Main method'''
    interface   = cmdi()
    args        = interface.parse_arguments(argument_dict)
    if args.ul:
        local_conn = llc()
        local_conn.connect_to_db()
        local_conn.query_local_zotero(collection_name=args.c)
        local_conn.get_local_copies(save_path=args.o)
    else:
        #downloading from Zotero api and scraping available full-text pdfs
        zc          = elc.connect_zotero(
            library_id=LIB_ID, 
            api_key=API_KEY, 
            library_type='user'
            )
        mapping     = elc.map_colname_colid_zotero(
            zotero_connection=zc, 
            collection_name=args.c, 
            depth=int(args.d), 
            force_run=args.fa
            )
        items       = elc.get_items_zotero(zc, mapping)
        pdf_url_map = elc.get_pdf_urls_zotero(
            items, 
            col_name=args.c, 
            force_run=args.fa
            )
        elc.download_files(args.o, pdf_url_map)

    pdf_gen     = pp.preprocess_generator(tp.pdf_generator(args.o), 
                                          output_path=os.path.join(args.o, 'wordclouds/'), 
                                          stemming_alg=stemming_algorithm, 
                                          ext_stopword_list=extended_stopword_list,
                                           n_gram_value=int(args.ng),
                                           wordclouds=args.wc,
                                           tf_plots=args.tfp,
                                           tokenizer=tokenizer_alg,
                                           lower_fth=lower_freq_th,
                                           upper_fth=upper_freq_th
                                           )
    docs,names = [],[]
    for doc in pdf_gen:
        docs.append(doc['result'])
        names.append(doc['name'])
    if args.tfp:
        pp.aggragate_tfs(output_path=args.o, n_gram_value=int(args.ng))
    vocab = pp.gen_vocab(docs)
    bow_gen     = pp.bow_generator(docs, vocab=vocab)
    corpus      = [bow for bow in bow_gen]

    pp.get_cooc_vocab(
            docs=docs, 
            vocab=vocab, 
            vocab_path=os.path.join(args.o, f'vocab_{args.ng}.txt'), 
            cooc_path=os.path.join(args.o,f'cooc_{args.ng}.txt'), 
            window=cooc_window_size
            )

    pp.save_corpus_to_vw(
        docs=docs,
        names=names,
        output_path=args.o,
        file_name=args.m
        )
    if not args.sm:
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
    else:
        print('Skipping topic modeling.')

    

if __name__ == "__main__":
    main()