import logging 
import re
import nltk
import concurrent.futures
import gensim.corpora as corpora
import os
import pandas as pd
import itertools

from collections import Counter
from spacy.tokenizer import Tokenizer
from spacy.lang.en import English
from nltk.stem import *
from nltk.corpus import stopwords
from nltk.util import ngrams
from wordcloud import WordCloud
from matplotlib import pyplot as plt
from glob import glob

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
    def clear_text_case_punct(pdf_dict:dict, tokenizer:str='nltk') -> dict:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        removes punctuation and converts all leters to lowercase.
        '''

        def max_dimer_freq(string):
                '''Dimer frequency scan to detect words made from single character and words of 2 characters'''
                max_freq = 0
                for i in range(len(string)-1):
                    dimer = string[i:i+2]
                    #counting overlapping dimers
                    count = len(re.findall(f'(?={dimer})', string))
                    if count > max_freq:
                        max_freq = count
                return round(max_freq/len(string),1)
        for k in pdf_dict:
            pdf_dict[k] = re.sub(r'([,.!?])([^\s])', r'\1 \2', pdf_dict[k])
            pdf_dict[k] = re.sub("\s{2,}", " ", pdf_dict[k])
            if tokenizer == 'nltk':
                pdf_dict[k] = nltk.word_tokenize(pdf_dict[k])
                pdf_dict[k] = [word.lower() for word in pdf_dict[k] if word.isalpha() and max_dimer_freq(word.lower()) < 0.5 and pdf_dict[k].count(word) > 3 and pdf_dict[k].count(word) < 950]
            elif tokenizer == 'spacy':
                nlp = English()
                tokenizer = nlp.tokenizer
                pdf_dict[k] = tokenizer(pdf_dict[k])
                pdf_dict[k] = [str(word).lower() for word in pdf_dict[k] if str(word).isalpha() and max_dimer_freq(word.lower()) < 0.5 and pdf_dict[k].count(word) > 3 and pdf_dict[k].count(word) < 950]
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
        stop_words = set([word.lower() for word in stopwords.words('english')] + [word.lower() for word in extended_list])
        for k in pdf_dict:
            pdf_dict[k] = [wd for wd in pdf_dict[k] if wd.lower() not in stop_words and len(wd) > 1]
        return pdf_dict
        # full_text = sum(pdf_dict.values(), [])
        # return [word for word in full_text if word not in stop_words]
    

    @staticmethod
    def generate_ngrams(pdf_dict:dict, n:int=2) -> list:
        if int(n) <=1:
            return [word for word in sum(pdf_dict.values(), [])]
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
    def get_cooc_vocab(docs, vocab, vocab_path, cooc_path, window=10)-> None:
        '''Generates vocabulary and cooccurence files to use in artm'''
        with open(vocab_path, 'w') as f:
            for _, word in vocab.iteritems():
                f.write(word + '\n')
        # Initialize a counter to hold co-occurrence counts.
        co_occurrences = Counter()

        for doc in docs:
            # Convert document tokens to their respective IDs using the Gensim dictionary.
            token_ids = [vocab.token2id[token] for token in doc if token in vocab.token2id]
            
            # For each token in the document, consider a window of 'window_size' tokens before and after.
            for i, token_id in enumerate(token_ids):
                window_start = max(i - window, 0)
                window_end = min(i + window + 1, len(token_ids))
                
                # Count co-occurrences within this window.
                for cooc_id in token_ids[window_start:window_end]:
                    # Avoid counting the word with itself.
                    if cooc_id != token_id:
                        # Sort the token IDs to ensure consistency (since ARTM co-occurrence data is symmetric).
                        pair = tuple(sorted((token_id, cooc_id)))
                        co_occurrences[pair] += 1

        with open(cooc_path, 'w') as f:
            for (word_id_1, word_id_2), count in co_occurrences.items():
                f.write(f"{word_id_1} {word_id_2} {count}\n")

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
        try:
            # Generate a word cloud
            logging.info(f'Generating wordcloud plot - {file_name}')
            if pdf_list:
                long_string = ','.join(pdf_list)
                wordcloud = WordCloud(background_color="white", max_words=5000, contour_width=3, contour_color='steelblue')
                wordcloud.generate(long_string)
                # Visualize the word cloud
                wordcloud.to_file(file_name)
            else:
                logging.warning(f'Cannot generate wordcloud plot for {file_name} - no words parsed from document.')
        except Exception as e:
            logging.error(f'Failed to generate word cloud for {file_name}')


    @staticmethod
    def plot_tfplot(pdf_list:list=[], pdf_df=None, file_name:str='test', top:int=100, save_pdf:bool=True) -> None:
        '''
        Given a document, represented as dictionary where page number is mapped to text,
        plots wordcloud showing most frequent word accross the entire dictionary.
        ''' 
        logging.info(f'Generating term frequency plot - {file_name}')
        try:
            if pdf_list and not os.path.isfile(file_name):
                if not os.path.isfile(file_name):
                    unique_terms = set(pdf_list)
                    term_counts = {term:pdf_list.count(term) for term in unique_terms}
                    df = pd.DataFrame(list(term_counts.items()), columns=['term', 'frequency'])
                    df = df.sort_values(by='frequency', ascending=False)
                    if save_pdf: 
                        df.to_csv(file_name.replace('.png','.csv'), header=True, index=False)
                    df = df.head(top)
                    plt.figure(figsize=(20, 45))
                    plt.barh(width = df.frequency, y=df.term)
                    plt.xlabel('term')
                    plt.ylabel('frequency')
                    plt.xticks(rotation=90)
                    plt.savefig(file_name, bbox_inches='tight')
                    plt.close()
                else:
                    logging.warning(f'Cannot generate term frequency plot for {file_name} - file already exists.')
            elif pdf_df is not None:
                df = pdf_df.head(top)
                plt.figure(figsize=(45, 11))
                plt.barh(width = df.frequency, y=df.term)
                plt.xlabel('term')
                plt.ylabel('frequency')
                plt.xticks(rotation=90)
                plt.savefig(file_name, bbox_inches='tight')
            else:
                logging.warning(f'Cannot generate term frequency plot for {file_name} - no words parsed from document.')
        except Exception as e:
            logging.error(f'Failed to generate term frequency for {file_name} - {e}')
        

    @staticmethod
    def preprocess_document(pdf_dict, file_name, image_path:str=None, stemming_alg:str='Porter', ext_stopword_list:list=[], n_gram_value:int=1, wordclouds=False, tf_plots=False, tokenizer='nltk') -> dict:
        '''
        Combining pre-processing into single method for convenience.
        '''
        pdf_dict = PreProcessor.clear_text_case_punct(pdf_dict, tokenizer=tokenizer)
        pdf_dict = PreProcessor.remove_stopwords(pdf_dict, extended_list=ext_stopword_list)
        pdf_dict = PreProcessor.stemming(pdf_dict, algorithm=stemming_alg)
        pdf_list = PreProcessor.generate_ngrams(pdf_dict, n=n_gram_value)

        fname = str(os.path.basename(file_name).replace('.pdf',''))
        wordcloud_path = os.path.join(image_path, fname) + f'{n_gram_value}.png'
        wc_condition = (image_path is not None) and (not os.path.isfile(wordcloud_path)) and wordclouds
        tf_condition = tf_plots
        if wc_condition:
            PreProcessor.plot_wordcloud(pdf_list=pdf_list, file_name=wordcloud_path)
        elif tf_condition:
            PreProcessor.plot_tfplot(pdf_list=pdf_list, file_name=wordcloud_path)
        return pdf_list


    @staticmethod
    def preprocess_generator(pdf_generator, output_path:str=None, stemming_alg:str='Porter', ext_stopword_list:list=[], n_gram_value:int=1, wordclouds=False, tf_plots=False, tokenizer='nltk'):
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
                wordclouds=wordclouds,
                tf_plots=tf_plots,
                tokenizer=tokenizer
                )}


    @staticmethod
    def aggragate_tfs(output_path:str, n_gram_value=1):
        '''Aggregating term frequencies for all documents in corpus.'''
        tag = os.path.join(output_path, 'wordclouds/') + f"*{n_gram_value}.csv"
        total_df = pd.DataFrame()
        for path in glob(tag):
            total_df = pd.concat([total_df, pd.read_csv(path)])
        total_df = total_df.groupby('term').agg('sum').reset_index().sort_values(by='frequency', ascending=False)
        if n_gram_value == 1:
            def max_char_freq(string):
                alphabet = set(string)
                max_freq = 0
                for c in alphabet:
                    freq = string.count(c)
                    if freq > max_freq:
                        max_freq = freq
                return  max_freq
            
            def max_dimer_freq(string):
                '''Dimer frequency scan to detect words made from single character and words of 2 characters'''
                max_freq = 0
                for i in range(len(string)-1):
                    dimer = string[i:i+2]
                    #counting overlapping dimers
                    count = len(re.findall(f'(?={dimer})', string))

                    if count > max_freq:
                        max_freq = count
                return round(max_freq/len(string),1)

            total_df['token_len'] = total_df['term'].apply(len)
            total_df['max_char_count'] = total_df['term'].apply(max_char_freq)
            total_df['max_dimer_freq'] = total_df['term'].apply(max_dimer_freq)
        total_df.to_csv(os.path.join(output_path,f'corpus_tf_{n_gram_value}.csv'), header=True, index=False)