import gensim.models
import pickle 
import pyLDAvis
import pyLDAvis.gensim
import os
import sys
import logging



'''
Development notes
'''
  
#######################
#General configurations
#######################


#######
#Models
#######

class LatentDirichletAllocation():
    '''LDA-related toolkit class'''

    @staticmethod
    def get_lda_model(corpus, vocab, num_topics):
        '''Wrapper for gensim.models.Lda to obtain the model trained to detect num_topics from corpus of documents'''
        return gensim.models.LdaMulticore(corpus=corpus,
                                       id2word=vocab,
                                       num_topics=num_topics)
    

    @staticmethod
    def load_lda_model(path):
        return gensim.models.LdaMulticore.load(path)
    

    @staticmethod
    def visualize_lda_model(model, corpus, vocab, output_path):
        # Visualize the topics
        # # this is a bit time consuming - make the if statement True
        # # if you want to execute visualization prep yourself
        if not os.path.isfile(output_path):
            try:
                LDAvis_prepared = pyLDAvis.gensim.prepare(model, corpus, vocab)
            except Exception as e:
                logging.error(f'Failed to visualize results for vanilla LDA - {e} - try adjusting number of topics')
                sys.exit(2)
            viz_path = os.path.abspath(os.path.join(output_path, 'phyloviz'))
            os.makedirs(viz_path,exist_ok=True)
            viz_path= os.path.join(viz_path, 'viz_' + str(model.num_topics) + '.pickle')
            with open(viz_path, 'wb') as f:
                pickle.dump(LDAvis_prepared, f)
            pyLDAvis.save_html(LDAvis_prepared, os.path.join(output_path,str(model.num_topics) +'.html'))

    
    @staticmethod
    def run_default_gensim_lda(corpus:list, vocab, model_path:str, num_topics:int=3, visualize_lda=True, visual_path:str=None):
        if not os.path.isfile(model_path):
            lda_model   = LatentDirichletAllocation.get_lda_model(corpus=corpus, vocab=vocab, num_topics=num_topics)
            lda_model.save(model_path)
        else:
            lda_model = LatentDirichletAllocation.load_lda_model(model_path)
        if visualize_lda:
            LatentDirichletAllocation.visualize_lda_model(model=lda_model, corpus = corpus, vocab=vocab, output_path=visual_path)
