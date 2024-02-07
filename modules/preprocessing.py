import logging 
import re
import nltk
import concurrent.futures
import gensim.corpora as corpora
import os


from nltk.stem import *
from nltk.corpus import stopwords
from wordcloud import WordCloud


'''
Development notes
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
    def stemming(pdf_dict:dict, algorithm:str='Porter') -> dict:
        '''
        Given a document, represented as dictionary where page number is mapped to TOKENIZED text,
        applies stemming to the text with specified algorithm implemented in nltk.
        '''
        if algorithm == 'Porter':
            stemmer = PorterStemmer()
        elif algorithm == 'Snowball':
            stemmer = snowball.SnowballStemmer('english')
        else:
            return pdf_dict
        
        for k in pdf_dict:
            pdf_dict[k] = [stemmer.stem(wd) for wd in pdf_dict[k]]
        return [word for word in sum(pdf_dict.values(), [])]


    @staticmethod
    def remove_stopwords(pdf_dict:dict, extended_list:list=[]) -> list:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        removes stopwords from the text.
        '''
        stop_words = stopwords.words('english')
        stop_words.extend(extended_list)
        for k in pdf_dict:
            pdf_dict[k] = [wd for wd in pdf_dict[k] if wd not in stop_words]
        return pdf_dict
        # full_text = sum(pdf_dict.values(), [])
        # return [word for word in full_text if word not in stop_words]
    

    @staticmethod
    def preprocess_generator(pdf_generator, output_path:str=None, stemming_alg:str='Porter', ext_stopword_list:list=[]):
        '''Preprocessing wrapper for pdf generator'''
        os.makedirs(output_path, exist_ok=True)
        if stemming_alg in ['Porter', 'Snowball']:
            logging.info(f'Running stemming using {stemming_alg} algorithm.')
        else:
            logging.warning(f'Unrecognized value was given for stemming algorithm - {stemming_alg} - stemming will be skipped.')
        for i,file in enumerate(pdf_generator):
            yield PreProcessor.preprocess_document(file, file_number=i+1, image_path=output_path, stemming_alg=stemming_alg, ext_stopword_list=ext_stopword_list)


    @staticmethod
    def preprocess_document(pdf_dict, file_number, image_path:str=None, stemming_alg:str='Porter', ext_stopword_list:list=[]) -> dict:
        '''
        Combining pre-processing into single method for conveniece.
        '''
        pdf_dict = PreProcessor.clear_text_case_punct(pdf_dict)
        pdf_dict = PreProcessor.remove_stopwords(pdf_dict,extended_list=ext_stopword_list)
        pdf_list = PreProcessor.stemming(pdf_dict, algorithm=stemming_alg)

        if image_path is not None:
            PreProcessor.plot_wordcloud(pdf_list=pdf_list, file_name=os.path.join(image_path, str(file_number) + '.png'))
        return pdf_list
    

    @staticmethod
    def gen_vocab(docs) -> set:
        '''
        Given a generator for documents represented as dictionary where page number is mapped to text,
        returns a set of unique words accross all documents.
        '''
        id2word = corpora.Dictionary(docs)
        return id2word


    @staticmethod
    def bow_generator(docs, vocab):
        '''Generator wrapper to get BOW representation for articles'''
        for doc in docs:
            yield PreProcessor.bag_of_words(doc, vocab)


    @staticmethod
    def bag_of_words(pdf_list:list, vocab:set) -> list:
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