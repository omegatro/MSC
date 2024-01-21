import gensim.models
import pyLDAvis.gensim
import pickle 
import pyLDAvis
import os

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
            LDAvis_prepared = pyLDAvis.gensim.prepare(model, corpus, vocab)
            viz_path = os.path.abspath(os.path.join(output_path, 'phyloviz'))
            os.makedirs(viz_path,exist_ok=True)
            viz_path= os.path.join(viz_path, 'viz_' + str(model.num_topics) + '.pickle')
            with open(viz_path, 'wb') as f:
                pickle.dump(LDAvis_prepared, f)
            pyLDAvis.save_html(LDAvis_prepared, os.path.join(output_path,str(model.num_topics) +'.html'))
