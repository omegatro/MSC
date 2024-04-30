# Introduction
This repository contains the code developed as a part of work on the following thesis: "UNSUPERVISED MACHINE LEARNING APPROACH FOR HIERARCHICAL GRAPH-BASED REPRESENTATION OF NATURAL LANGUAGE TEXT COLLECTIONS"
It consists of python scripts for data preprocessing, as well as jupyter notebooks outlining the learning process and summarizing final results. Additionally the preprocessed data were made available.

## Setup & Installation

- Prerequisites
   - [Anaconda](https://www.anaconda.com/download)
   - [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install)
   - [Zotero](https://www.zotero.org/download/)
   - [Zotero private API key](https://www.zotero.org/settings/keys) available in ```<path_to_MSC_folder>/MSC/.secrets``` file
- Installation
```
git clone https://github.com/omegatro/MSC
cd <path_to_MSC_folder>/MSC/
conda env create -f msc_project_env.yaml
```
- Command-line interface for preprocessing
```
options:
  -h, --help            show this help message and exit
  --l, --library_name
                        Name of the Zotero library to parse.
  --c, --collection_name
                        Name of the Zotero collection to parse
  --m, --model_file_name
                        Name of model to name the files (required for compatibility with genism LDA module)
  --ng, --nram_len  Length of the n-gram
  --ul, --use_local     Flag to analyze locally-stored copies of publications instead of downloading from links.
  --sm, --skip_model    Flag to skip LDA topic modelling
  --wc, --word_clouds   Flag to generate wordcloud plot for each pdf file
  --tfp, --tf_plots     Flag to generate term frequency bar plot for each pdf file

Required arguments:
  --o, --output_path
                        Full path to the folder where the downloaded files should be saved.
```
- Command example:
```
python main.py --l 'My Library' --o ./Data/bioit_set/ --c 'Bioinformatics set' --m nlp_set_1 --sm --ng 1 --ul
```
- Results
   - [Visual results](https://github.com/omegatro/MSC/blob/main/results/Final_results.ipynb) include hARTM topic models and plots generated based on those models.
   - [Preliminary results](https://github.com/omegatro/MSC/blob/main/results/Preliminary_results.html) presented at [RaTSIf conference](https://ratsif.tsi.lv/ratsif-2024-spring/)
- Datasets
   - Contains two preprocessed datasets from the thesis:
      - [Bioinformatics dataset](https://github.com/omegatro/MSC/tree/main/public_data/bioit_set)
      - [NLP dataset](https://github.com/omegatro/MSC/tree/main/public_data/nlp_set)
   - Each dataset contains:
      - Unigram total frequency for each dataset (files with tf_1.csv suffix).
      - Bigram-based representation for each document in Vowpal-Wabbit format (files with _vw.txt suffix).
      - Bigram co-occurrence count dictionary used for coherence calculations (cooc_2.txt).
      - Vocabulary of unique bigrams for each dataset (vocab_2.txt).
