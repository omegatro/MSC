import logging 
import re
import nltk

from nltk.corpus import stopwords
from wordcloud import WordCloud

'''
Development notes
1. Add logging
'''

#######################
#General configurations
#######################

logging.basicConfig(level=1)
# nltk.download('punkt')
# nltk.download('stopwords')

###############
#Pre-processing
###############

class PreProcessor():
    '''
    Toolkit class to store methods for text pre-processing
    '''
    @staticmethod
    def combine_text(pdf_dict:dict) -> str:
        '''
        Helper function to combine text into one string, 
        given a document, represented as dictionary where page number is mapped to text,
        '''
        full_text = ''
        for k in pdf_dict:
            full_text += pdf_dict[k]
        return full_text

    
    @staticmethod
    def clear_text_case_punct(pdf_dict:dict) -> dict:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        removes punctuation and converts all leters to lowercase.
        '''
        for k in pdf_dict:
            pdf_dict[k] = nltk.word_tokenize(pdf_dict[k])
            pdf_dict[k] = [word.lower() for word in pdf_dict[k] if word.isalpha()]
        return pdf_dict

    
    @staticmethod
    def remove_stopwords(pdf_dict:dict) -> dict:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        removes stopwords from the text.
        '''
        stop_words = stopwords.words('english')
        stop_words.extend(['from', 'subject', 're', 'edu', 'use'])
        for k in pdf_dict:
            pdf_dict[k] = [word for word in pdf_dict[k] if word not in stop_words]
        return pdf_dict
    

    @staticmethod
    def preprocess_document(pdf_dict) -> dict:
        '''
        Combining pre-processing into single method for conveniece.
        '''
        pdf_dict = PreProcessor.clear_text_case_punct(pdf_dict)
        pdf_dict = PreProcessor.remove_stopwords(pdf_dict)
        return pdf_dict


    @staticmethod
    def gen_vocab(pdf_generator) -> set:
        '''
        Given a generator for documents represented as dictionary where page number is mapped to text,
        returns a set of unique words accross all documents.
        '''
        vocab = set()
        for doc in pdf_generator:
            d = PreProcessor.preprocess_document(doc)
            full_text = sum(d.values(), [])
            vocab = vocab.union(set(full_text))
        return vocab
        

    @staticmethod
    def bag_of_words(pdf_dict:dict, vocab:set) -> list:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        returns bag-of-words in a form of a list.
        '''
        full_text = sum(pdf_dict.values(), [])
        return {wd:full_text.count(wd) for wd in vocab}


    @staticmethod
    def plot_wordcloud(pdf_dict:dict, file_name:str='test.png') -> None:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        plots wordcloud showing most frequent word accross the entire dictionary.
        '''
        long_string = ','.join(sum(pdf_dict.values(), []))
        wordcloud = WordCloud(background_color="white", max_words=5000, contour_width=3, contour_color='steelblue')
        # Generate a word cloud
        wordcloud.generate(long_string)
        # Visualize the word cloud
        wordcloud.to_file(file_name)