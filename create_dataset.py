import pandas as pd
import numpy as np
from rake_nltk import Rake
import json
import ast
import csv
import os.path
from functions import *
from paper import Paper


def create_csv_copy(filename, check):
    test_title = None
    df = pd.read_csv(filename, sep=',', encoding='ISO-8859-1')
    new_filename = 'user_plus.csv'
    df.to_csv(new_filename, index = False)
    with open(new_filename, 'a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',')
        paper = scrapeLingBuzzHomePage(check)
        if paper.title == 'dummy':
            return False
        try:
            filewriter.writerow([paper.title, paper.link, paper.authors, paper.abstract, paper.keywords])
            test_title = paper.title
        except UnicodeEncodeError:
            print(paper.title[:31]+'...\'', 'skipped')
            return False
    return test_title

def clean_authors(author_list):
    return [author.lower().strip().replace(' ', '').replace(',', '') for author in author_list]

def create_csv():
    """Creates an initial user-specific dataset (`user.csv`) of papers from
    LingBuzz according to keywords in `config.json`."""
    if os.path.isfile('user.csv'):
        print ("User model found")
        return
    else:
        pass
    print("Fetching papers ... this may take a few minutes.")
    # open config file to get user-entered parameters
    f = open('config.json', 'r')
    obj = f.read()
    config = json.loads(obj)
    f.close()

    # find papers from LingBuzz matching user preferences
    collected_papers = []
    for term in config['keywords']:
        try:
            papers_to_add = queryLingBuzz(term)
            collected_papers.extend(papers_to_add)
            print("\'" + term + "\' query finished")
        except:
            print('No results found for', term)
            continue

    # create csv dataset file with relevant papers
    with open('user.csv', 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',')
        filewriter.writerow(['Title', 'Link', 'Authors', 'Abstract', 'Keywords'])
        skipped = 0
        for paper in collected_papers:
            # Catch potential UnicodeEncodeError (certain characters don't want to be written in csv files)
            try:
                filewriter.writerow([paper.title, paper.link, paper.authors, paper.abstract, paper.keywords])
            except UnicodeEncodeError:
                #print('UnicodeEncodeError: \'' + paper.title[:31]+'...\'', 'skipped')
                skipped += 1
                continue
    #print('Skipped to UnicodeDecodeError:', skipped)
    print('Done')


def create_df():
    """Returns a pandas dataframe object created accoring to `user.csv`."""
    #print("Creating initial user dataframe ...")
    # encoding='ISO-8859-1' is used here to prevent UnicodeDecodeError
    df = pd.read_csv('user_plus.csv', sep=',', encoding='ISO-8859-1')
    df = df[['Title', 'Link', 'Authors', 'Abstract', 'Keywords']]

    return df


def merge_df(df):
    """Merges columns in a dataframe of LingBuzz papers into one bag_of_words
    column. The resulting dataframe is organized into two columns : (Title | bag_of_words).

    Parameters
    ----------
    df : dataframe to be merged by column into one bag_of_words column
    """
    #print("Extracting keywords from papers ...")
    # create new column which relevant columns (Authors, Abstract, Keywords) will be collapsed into
    df['bag_of_words'] = ''

    for index, row in df.iterrows():
        # create empty list to which final key words are added per paper
        bag_of_words_list = []

        # collect Authors column
        authors = row['Authors']
        author_list = ast.literal_eval(authors)
        # clean each author in the author list
        author_list = clean_authors(author_list)
        # add authors to bag_of_words_list
        bag_of_words_list.extend(author_list)

        # collect Abstract column
        abstract = row['Abstract']
        # first extract keywords from Abstract column via nltk's Rake
        r = Rake()
        r.extract_keywords_from_text(abstract)
        keywords_dict_scores = dict(r.get_word_degrees())
        abstract_keywords = list(keywords_dict_scores.keys())
        # add abstract_keywords to bag_of_words_list
        bag_of_words_list.extend(abstract_keywords)

        # collect Keywords column
        keywords = row['Keywords']
        keywords_list = ast.literal_eval(keywords)
        # add keywords to bag_of_words_list
        bag_of_words_list.extend(keywords_list)

        words = ''
        for word in bag_of_words_list:
            words = words + ' ' + word
        # add everything to bag_of_words column for current paper
        df.at[index, 'bag_of_words'] = words

    # drop columns
    df.drop(columns = ['Authors', 'Abstract', 'Keywords'], inplace=True)
    #print('Done')
    return df

#create_csv_copy('user.csv')
