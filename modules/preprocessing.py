import logging 
import re
import nltk
import concurrent.futures
import gensim.corpora as corpora
import os

from nltk.stem import *
from nltk.corpus import stopwords
from nltk.util import ngrams
from wordcloud import WordCloud


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
        return pdf_dict


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
    def generate_ngrams(pdf_dict:dict, n:int=2) -> dict:
        if n <=1:
            return pdf_dict
        for k in pdf_dict:
            pdf_dict[k] = ["_".join(ngram) for ngram in ngrams([wd for wd in pdf_dict[k]], n)]
        return [word for word in sum(pdf_dict.values(), [])]


    @staticmethod
    def save_corpus_to_vw(docs, names, output_path, file_name):
        '''Saves the entire corpus in Vowpal Wabbit format to a specified file.'''
        logging.info('Saving dataset to Vowpal Wabbit file to be used with BigARTM.')
        output = os.path.join(output_path, f'{file_name}_vw.txt')
        with open(output, 'w') as vw_file:  # Use 'w' to overwrite or create a new file
            for idx, doc in enumerate(docs):
                # Use the abstracted method to save each document
                PreProcessor.save_document_to_vw(vw_file, names[idx], doc)


    @staticmethod
    def save_document_to_vw(vw_file, doc_name, doc):
        '''Formats and writes a single document's bag of words to the VW format file.'''
        # Assuming a default label of 1 for simplicity
        vw_line = os.path.basename(doc_name).replace('.pdf', '').replace(' ', '_') # Format the document identifier
        # Add word-frequency pairs, format as "word:frequency" if frequency > 1, else just "word"
        if len(doc) > 0:
            for wd in doc:
                vw_line += f" {wd}"
        # Write the formatted line to the VW file
        vw_file.write(vw_line + "\n")


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
    def plot_wordcloud(pdf_list:list, file_name:str='test') -> None:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        plots wordcloud showing most frequent word accross the entire dictionary.
        ''' 
        logging.info(f'Generating wordcloud plot - {file_name}')
        long_string = ','.join(pdf_list)
        wordcloud = WordCloud(background_color="white", max_words=5000, contour_width=3, contour_color='steelblue')
        
        try:
            # Generate a word cloud
            if len(long_string) > 0:
                wordcloud.generate(long_string)
                # Visualize the word cloud
                wordcloud.to_file(file_name)
            else:
                logging.warning(f'Cannot generate wordcloud plot for {file_name} - no words parsed from document.')
        except Exception as e:
            logging.error(f'Failed to generate word cloud for {file_name}')


    @staticmethod
    def preprocess_document(pdf_dict, file_name, image_path:str=None, stemming_alg:str='Porter', ext_stopword_list:list=[], n_gram_value:int=1, wordclouds=False) -> dict:
        '''
        Combining pre-processing into single method for convenience.
        '''
        pdf_dict = PreProcessor.clear_text_case_punct(pdf_dict)
        pdf_dict = PreProcessor.remove_stopwords(pdf_dict, extended_list=ext_stopword_list)
        pdf_dict = PreProcessor.stemming(pdf_dict, algorithm=stemming_alg)
        pdf_list = PreProcessor.generate_ngrams(pdf_dict, n=n_gram_value)

        fname = str(os.path.basename(file_name).replace('.pdf',''))
        wordcloud_path = os.path.join(image_path, fname) + '.png'
        wc_condition = (image_path is not None) and (not os.path.isfile(wordcloud_path)) and wordclouds
        if wc_condition:
            PreProcessor.plot_wordcloud(pdf_list=pdf_list, file_name=wordcloud_path)
        return pdf_list


    @staticmethod
    def preprocess_generator(pdf_generator, output_path:str=None, stemming_alg:str='Porter', ext_stopword_list:list=[], n_gram_value:int=1, wordclouds=False):
        '''Preprocessing wrapper for pdf generator'''
        os.makedirs(output_path, exist_ok=True)
        logging.info('Starting preprocessing.')
        if stemming_alg in ['Porter', 'Snowball']:
            logging.info(f'Running stemming using {stemming_alg} algorithm.')
        else:
            logging.warning(f'Unrecognized value was given for stemming algorithm - {stemming_alg} - stemming will be skipped.')
        for file in pdf_generator:
            yield {'name':file['name'], 'result':PreProcessor.preprocess_document(
                pdf_dict=file['text'], 
                file_name=file['name'], 
                image_path=output_path, 
                stemming_alg=stemming_alg, 
                ext_stopword_list=ext_stopword_list, 
                n_gram_value=n_gram_value,
                wordclouds=wordclouds
                )}
