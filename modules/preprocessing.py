import logging 
import re
import nltk
import concurrent.futures
import gensim.corpora as corpora
import os

from nltk.corpus import stopwords
from wordcloud import WordCloud

'''
Development notes
1. Add logging
'''

#######################
#General configurations
#######################

logging.basicConfig(level=2)
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
    def remove_stopwords(pdf_dict:dict) -> list:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        removes stopwords from the text.
        '''
        stop_words = stopwords.words('english')
        stop_words.extend(['from', 'subject', 're', 'edu', 'use', 'et', 'al', 'pp'])
        full_text = sum(pdf_dict.values(), [])
        return [word for word in full_text if word not in stop_words]
    

    @staticmethod
    def preprocess_generator(pdf_generator):
        '''Preprocessing wrapper for pdf generator'''
        for i,file in enumerate(pdf_generator):
            yield PreProcessor.preprocess_document(file, file_number=i+1)


    @staticmethod
    def preprocess_document(pdf_dict, file_number, image_path=r"C:\Users\omegatro\Desktop\MSC\Data\test\wordclouds\\") -> dict:
        '''
        Combining pre-processing into single method for conveniece.
        '''
        pdf_dict = PreProcessor.clear_text_case_punct(pdf_dict)
        pdf_list = PreProcessor.remove_stopwords(pdf_dict)
        if not os.path.isfile(fr'{image_path}{file_number}.png'):
            PreProcessor.plot_wordcloud(pdf_list=pdf_list, file_name=fr'C:\Users\omegatro\Desktop\MSC\Data\test\wordclouds\{file_number}.png')
        return pdf_list
    

    @staticmethod
    def gen_vocab(pdf_generator) -> set:
        '''
        Given a generator for documents represented as dictionary where page number is mapped to text,
        returns a set of unique words accross all documents.
        '''
        id2word = corpora.Dictionary([doc for doc in pdf_generator])
        return id2word


    @staticmethod
    def bow_generator(pdf_generator, vocab):
        '''Generator wrapper to get BOW representation for articles'''
        for doc in pdf_generator:
            yield PreProcessor.bag_of_words(doc, vocab)


    @staticmethod
    def bag_of_words(pdf_list:dict, vocab:set) -> list:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        returns bag-of-words in a form of a list of tuples containing index of a word in a document and number of times it appears.
        '''
        return vocab.doc2bow(pdf_list)


    @staticmethod
    def plot_wordcloud(pdf_list:list, file_name:str='test.png') -> None:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        plots wordcloud showing most frequent word accross the entire dictionary.
        '''
        long_string = ','.join(pdf_list)
        wordcloud = WordCloud(background_color="white", max_words=5000, contour_width=3, contour_color='steelblue')
        # Generate a word cloud
        wordcloud.generate(long_string)
        # Visualize the word cloud
        wordcloud.to_file(file_name)