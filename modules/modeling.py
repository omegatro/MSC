import gensim.models

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