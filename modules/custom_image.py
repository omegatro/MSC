import pandas as pd
import glob
import os
import re
from matplotlib import pyplot as plt

# DATASET_PATH = os.path.abspath('Data/nlp_set/nlp_set_2_vw.txt')
# METADATA_PATH = os.path.abspath('Data/metadata/NLP_set.csv')
# WORDCLOUD_PATH = os.path.abspath('Data/nlp_set/wordclouds/')


DATASET_PATH = os.path.abspath('Data/nlp_set/nlp_set_2_vw.txt')
METADATA_PATH = os.path.abspath('Data/metadata/nlp_set.csv')
WORDCLOUD_PATH = os.path.abspath('Data/nlp_set/wordclouds/')

def add_ngram_tags(set_name, n=2, n_tags=10):
    # Step 1: Read the metadata CSV into a DataFrame
    metadata_df = pd.read_csv(METADATA_PATH)

    # Step 2: Get a list of all n-gram CSV filenames
    ngram_files = glob.glob(f'{WORDCLOUD_PATH}/*{n}.csv')
    print(f'Found {len(ngram_files)} files matching n-gram pattern.')

    # Function to extract the partial name by splitting with ' - ' and trimming '{n}.csv'
    def extract_partial_name_from_filename(filename):
        base_name = os.path.basename(filename)
        parts = base_name.split(' - ')
        if len(parts) > 1:
            # Assume the format is always correct and split accordingly
            partial_name = re.sub(r'\d+\.csv', '', parts[-1]).strip()
            return partial_name.lower()  # Return lowercased partial name for case-insensitive matching
        return ''

    # Function to find the most similar title for the given partial name
    def find_most_similar_title(partial_name, titles):
        # Here you might implement a more sophisticated matching algorithm
        # For simplicity, this example uses simple substring matching
        fixed_part_name = re.sub(r'[^\w\s]', '' ,partial_name)
        for title in titles:
            fixed_title = re.sub(r'[^\w\s]', '' ,title.lower())
            if fixed_part_name in fixed_title:
                return title
        return None

    # Step 3: Match each document to its bigram CSV and extract top-10 bigrams
    ngram_tags = []
    for doc_name in metadata_df['Title']:
        # Extract all titles for comparison
        titles = metadata_df['Title'].tolist()
        # Find the file that best matches the document title
        best_file = None
        for file in ngram_files:
            partial_name = extract_partial_name_from_filename(file)
            
            if find_most_similar_title(partial_name, titles) == doc_name:
                best_file = file
                break

        if best_file:
            # Read the corresponding bigram CSV
            bigram_df = pd.read_csv(best_file)
            # Assuming bigram_df has 'term' and 'frequency' columns
            top_ngrams = bigram_df.nlargest(n_tags, 'frequency')['term'].tolist()
            ngram_tags.append('; '.join(top_ngrams))  # Convert list of bigrams to a semicolon-separated string
        else:
            ngram_tags.append('No Match Found')

    # Step 4: Add the bigram tags to the metadata DataFrame
    metadata_df[f'{n}_tags'] = ngram_tags

    # Optionally, save the updated metadata DataFrame to a new CSV
    updated_path = os.path.join(os.path.dirname(METADATA_PATH), f"{set_name}_set_{n}grammed.csv")
    metadata_df.to_csv(updated_path, index=False)
    print(f'Updated metadata with {n}-gram tags saved to: {updated_path}')

def main(meta_path, n, image_customization):
    """
    meta_path: path to the metadata CSV file
    n: n-gram (used for tags)
    image_customization: a dictionary containing customization options for each plot, including save paths
    """
    with open(DATASET_PATH, 'r+') as f:
        data = f.readlines()
    metadata = pd.read_csv(meta_path)
    count_dict = {l.split(' ')[0]: len(l.split(' ')[1:]) for l in data}
    count_df = pd.DataFrame.from_dict(count_dict, orient='index').reset_index()
    count_df.columns = ['name', 'bigram_counts']

    # Bigram frequency histogram
    fig, ax = plt.subplots(figsize=image_customization['bigram_histogram']['figsize'])
    count_df[['bigram_counts']].plot.hist(bins=25, legend=False, ax=ax)
    ax.set_ylabel('Document frequency')
    ax.set_xlabel('Bigram count')
    plt.savefig(image_customization['bigram_histogram']['save_path'])
    plt.close()

    # Documents by publication year
    by_year = metadata.groupby('Publication Year').count().rename(columns={'Key': 'Document frequency'})[['Document frequency']]
    fig, ax = plt.subplots(figsize=image_customization['by_year']['figsize'])
    by_year.plot.bar(legend=False, ax=ax, width=0.85)
    ax.set_ylabel('Document frequency', fontsize=image_customization['label_size_axis'])
    ax.set_xlabel('Publication year', fontsize=image_customization['label_size_axis'])
    plt.xticks(rotation=image_customization['by_year']['xticks_rotation'], rotation_mode='anchor', ha='right')
    ax.tick_params(axis='x', labelsize=image_customization['label_size_ticks'])  # Set x-axis tick label font size
    ax.tick_params(axis='y', labelsize=image_customization['label_size_ticks'])  # Set y-axis tick label font size
    plt.savefig(image_customization['by_year']['save_path'])
    plt.close()

    # Documents by journal abbreviation
    by_journal = metadata.groupby('Journal Abbreviation').count().rename(columns={'Key': 'Document frequency'})[['Document frequency']].sort_values('Document frequency', ascending=False)
    fig, ax = plt.subplots(figsize=image_customization['by_journal']['figsize'])
    by_journal.plot.bar(legend=False, ax=ax)
    ax.set_ylabel('Document frequency', fontsize=image_customization['label_size_axis'])
    ax.set_xlabel('Journal Name', fontsize=image_customization['label_size_axis'])
    ax.tick_params(axis='x', labelsize=image_customization['label_size_ticks'])  # Set x-axis tick label font size
    ax.tick_params(axis='y', labelsize=image_customization['label_size_ticks'])  # Set y-axis tick label font size
    # Adjust the bottom margin
    plt.subplots_adjust(bottom=0.20)  # Increase the value as needed to fit the labels
    plt.xticks(rotation=image_customization['by_journal']['xticks_rotation'], rotation_mode='anchor', ha='right')
    plt.savefig(image_customization['by_journal']['save_path'])
    plt.close()

    # Number of rows by tag
    tags = metadata[[f'{n}_tags']]
    exploded_tags = tags[f'{n}_tags'].str.split('; ').explode()
    tag_counts = exploded_tags.value_counts().head(50)
    fig, ax = plt.subplots(figsize=image_customization['tags']['figsize'])
    tag_counts.plot(kind='bar', ax=ax)
    ax.tick_params(axis='x', labelsize=image_customization['label_size_ticks'])  # Set x-axis tick label font size
    ax.tick_params(axis='y', labelsize=image_customization['label_size_ticks'])  # Set y-axis tick label font size
    ax.set_xlabel('Tag', fontsize=image_customization['label_size_axis'])
    ax.set_ylabel('Number of documents', fontsize=image_customization['label_size_axis'])
    plt.subplots_adjust(bottom=0.20)  # Increase the value as needed to fit the labels
    plt.xticks(rotation=image_customization['tags']['xticks_rotation'], rotation_mode='anchor', ha='right')
    plt.savefig(image_customization['tags']['save_path'])
    plt.close()

if __name__ == "__main__":
    n = 2
    dataset = 'NLP'
    meta_path = os.path.join(os.path.dirname(METADATA_PATH), f"{dataset}_set_{n}grammed.csv")
    if not os.path.isfile(meta_path):
        add_ngram_tags(set_name=dataset)
    image_customization = {
        'bigram_histogram': {'save_path': f'{os.path.dirname(METADATA_PATH)}/{dataset}_{n}gram_histogram.png', 'figsize': (15, 10)},
        'by_year': {'save_path': f'{os.path.dirname(METADATA_PATH)}/{dataset}_by_year.png', 'figsize': (15, 7.5), 'xticks_rotation': 0},
        'by_journal': {'save_path': f'{os.path.dirname(METADATA_PATH)}/{dataset}_by_journal.png', 'figsize': (20, 15), 'xticks_rotation': 35},
        'tags': {'save_path': f'{os.path.dirname(METADATA_PATH)}/{dataset}_tags.png', 'figsize': (20, 15), 'xticks_rotation': 45},
        'label_size_ticks': 12,
        'label_size_axis': 14
    }
    main(meta_path,n, image_customization)