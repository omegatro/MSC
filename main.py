from modules.input_parsing import CMDInterface as cmdi, ExternalLibConnector as elc, TextParser as tp
from modules.config import argument_dict, API_KEY, LIB_ID
from modules.preprocessing import PreProcessor as pp
from modules.modeling import LatentDirichletAllocation as lda
import os


def main():
    #downloading from Zotero api and scraping available full-text pdfs
    interface   = cmdi()
    args        = interface.parse_arguments(argument_dict)
    zc          = elc.connect_zotero(library_id=LIB_ID, api_key=API_KEY, library_type='user')
    mapping     = elc.map_colname_colid_zotero(zotero_connection=zc)
    items       = elc.get_items_zotero(zc, mapping, subset=[args.l])
    pdf_url_map = elc.get_pdf_urls_zotero(items)
    elc.download_files(args.o, pdf_url_map)
    pdf_gen     = pp.preprocess_generator(tp.pdf_generator(args.o))
    vocab       = pp.gen_vocab(pdf_gen)
    bow_gen     = pp.bow_generator(pp.preprocess_generator(tp.pdf_generator(args.o)), vocab=vocab)
    corpus      = [doc for doc in bow_gen]
    if not os.path.isfile('./models/lda.model'):
        lda_model   = lda.get_lda_model(corpus=corpus, vocab=vocab, num_topics=3)
        lda_model.save('./models/lda.model')
    else:
        lda_model = lda.load_lda_model('./models/lda.model')
    lda.visualize_lda_model(model=lda_model, corpus = corpus, vocab=vocab)




    

if __name__ == "__main__":
    main()