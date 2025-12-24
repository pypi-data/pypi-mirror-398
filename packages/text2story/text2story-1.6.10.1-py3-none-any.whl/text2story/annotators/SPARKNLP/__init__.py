'''
    SPARKNLP annotator

    Used for actor extraction
        'pt' : wikiner_6B_100
        'en' : default
'''

from text2story.core.utils import chunknize_actors
from text2story.core.exceptions import InvalidLanguage

import sparknlp
from pyspark.sql import SparkSession
from sparknlp.base import DocumentAssembler, LightPipeline
from sparknlp.annotator import Tokenizer, PerceptronModel, WordEmbeddingsModel, NerDLModel, NerCrfModel, SentenceDetector, RoBertaForTokenClassification
from pyspark.ml import Pipeline
import pandas as pd

import os

pipeline = {}

def load_embeddings():

    current_path = os.path.dirname(os.path.abspath(__file__))
    #embeddings_path = os.path.join("cache","glove_100d")
    embeddings_path = os.path.join("cache","glove_840B_300")
    embeddings_path = os.path.join(current_path, embeddings_path)

    embeddings = None

    if os.path.exists(embeddings_path):
        # cache the pretrained model to speed up local computations
        print("Loading local model of glove_840B_300")
        embeddings = WordEmbeddingsModel.load(embeddings_path)
    else:
        # downloading and saving the pre-trained model

        # embeddings = WordEmbeddingsModel.pretrained('glove_100d').setInputCols(["token", "document"]).setOutputCol("embeddings")
        embeddings = WordEmbeddingsModel.pretrained("glove_840B_300", "xx").setInputCols(["document","token"]).setOutputCol("embeddings")

        if not(os.path.exists(os.path.join(current_path,"cache"))):
            os.mkdir(os.path.join(current_path, "cache"))

        print("Saving %s locally..." % embeddings_path)
        embeddings.save(embeddings_path)

    return embeddings

def load_postagger_pt():

    current_path = os.path.dirname(os.path.abspath(__file__))
    postagger_path = os.path.join("cache","pos_ud_bosque")
    postagger_path = os.path.join(current_path, postagger_path)

    postagger = None

    if os.path.exists(postagger_path):
        # cache the pretrained model to speed up local computations
        print("Loading local model of pos_ud_bosque")
        postagger = PerceptronModel.load(postagger_path)
    else:
        # downloading and saving the pre-trained model

        postagger     = PerceptronModel.pretrained('pos_ud_bosque', 'pt').setInputCols(["document","token"]).setOutputCol("pos")

        if not(os.path.exists(os.path.join(current_path,"cache"))):
            os.mkdir(os.path.join(current_path, "cache"))

        print("Saving %s locally..." % postagger_path)
        postagger.save(postagger_path)

    return postagger

def load_postagger_en():

    current_path = os.path.dirname(os.path.abspath(__file__))
    postagger_path = os.path.join("cache","pos_anc")
    postagger_path = os.path.join(current_path, postagger_path)

    postagger = None

    if os.path.exists(postagger_path):
        # cache the pretrained model to speed up local computations
        print("Loading local model of pos_anc")
        postagger = PerceptronModel.load(postagger_path)
    else:
        # downloading and saving the pre-trained model

        postagger     = PerceptronModel.pretrained('pos_anc', 'en').setInputCols(["token", "document"]).setOutputCol("pos")

        if not(os.path.exists(os.path.join(current_path,"cache"))):
            os.mkdir(os.path.join(current_path, "cache"))

        print("Saving %s locally..." % postagger_path)
        postagger.save(postagger_path)

    return postagger

def load_ner_en():

    current_path = os.path.dirname(os.path.abspath(__file__))
    ner_path = os.path.join("cache","neren")
    ner_path = os.path.join(current_path, ner_path)

    postagger = None

    if os.path.exists(ner_path):
        # cache the pretrained model to speed up local computations
        print("Loading local model of NER en")
        ner = NerCrfModel.load(ner_path)
    else:
        # downloading and saving the pre-trained model

        ner      = NerCrfModel.pretrained().setInputCols(["document", "token", "pos", "embeddings"]).setOutputCol("ner")

        if not(os.path.exists(os.path.join(current_path,"cache"))):
            os.mkdir(os.path.join(current_path, "cache"))

        print("Saving %s locally..." % ner_path)
        ner.save(ner_path)

    return ner

def load_ner_pt():

    current_path = os.path.dirname(os.path.abspath(__file__))
    #ner_path = os.path.join("cache","wikiner")
    #ner_path = os.path.join("cache","roberta_ner_pt")
    ner_path = os.path.join("cache","wikiner_840B_300")
    ner_path = os.path.join(current_path, ner_path)

    postagger = None

    if os.path.exists(ner_path):
        # cache the pretrained model to speed up local computations
        print("Loading local model of Roberta NER PT")
        ner = NerDLModel.load(ner_path)
        #ner = NerCrfModel.load(ner_path)
        #ner = RoBertaForTokenClassification.load(ner_path)
    else:
        # downloading and saving the pre-trained model

        ner = NerDLModel.pretrained("wikiner_840B_300", 'pt').setInputCols(['document', 'token', 'embeddings']).setOutputCol('ner')

        #ner = RoBertaForTokenClassification.pretrained("wikiner_840B_300","pt").setInputCols(["sentence", "token"]).setOutputCol("ner")

        #ner      = NerDLModel.pretrained('wikiner_6B_100', 'pt').setInputCols(["document", "token", "embeddings"]).setOutputCol("ner")

        if not(os.path.exists(os.path.join(current_path,"cache"))):
            os.mkdir(os.path.join(current_path, "cache"))

        print("Saving %s locally..." % ner_path)
        ner.save(ner_path)

    return ner

def load(lang):
    """
    Used, at start, to load the pipeline for the supported languages.
    """

    #sparknlp.start(spark32=True)
    sparknlp.start()
    spark = SparkSession.builder.appName("t2s").getOrCreate()
    spark.sparkContext.setLogLevel("FATAL")

    documentAssembler = DocumentAssembler().setInputCol("text").setOutputCol("document")

    sentence_detector = SentenceDetector().setInputCols(["document"]).setOutputCol("sentence")

    tokenizer         = Tokenizer().setInputCols(["sentence"]).setOutputCol("token")

    # TODO: esse embeddings sao em ingles, usar em pt. Por isso que deve estar dando aquele erro
    # para portugues!
    embeddings = load_embeddings()

    if lang == "pt":
        pos_tagger_pt     = load_postagger_pt()
        ner_model_pt      = load_ner_pt()
        pipeline_pt = Pipeline(stages=[documentAssembler, sentence_detector,tokenizer, embeddings, pos_tagger_pt, ner_model_pt])
        pipeline['pt'] = LightPipeline(pipeline_pt.fit(spark.createDataFrame(pd.DataFrame({'text': ['']}))))
    elif lang == "en":
        pos_tagger_en     = load_postagger_en()
        ner_model_en      = load_ner_en()
        pipeline_en = Pipeline(stages=[documentAssembler, sentence_detector, tokenizer, embeddings, pos_tagger_en, ner_model_en])
        pipeline['en'] = LightPipeline(pipeline_en.fit(spark.createDataFrame(pd.DataFrame({'text': ['']}))))
    else:
        raise InvalidLanguage(lang)


def extract_actors(lang, text):
    """
    Parameters
    ----------
    lang : str
        the language of text to be annotated
    text : str
        the text to be annotated
    
    Returns
    -------
    list[tuple[tuple[int, int], str, str]]
        the list of actors identified where each actor is represented by a tuple

    Raises
    ------
        InvalidLanguage if the language given is invalid/unsupported
    """

    if lang not in ['pt', 'en']:
        raise InvalidLanguage

    doc = pipeline[lang].fullAnnotate(text)[0] 

    iob_token_list = []
    for i in range(len(doc['token'])):
        start_char_offset = doc['token'][i].begin
        end_char_offset   = doc['token'][i].end + 1
        char_span         = (start_char_offset, end_char_offset)
        pos_tag           = normalize(doc['pos'][i].result)
        ne                = doc['ner'][i].result[:2] + normalize(doc['ner'][i].result[2:]) if doc['ner'][i].result[:2] != 'O' else 'O'

        iob_token_list.append((char_span, pos_tag, ne))

    actor_list = chunknize_actors(iob_token_list)

    return actor_list


def normalize(label):
    """
    Parameters
    ----------
    label : str
    
    Returns
    -------
    str
        the label normalized
    """

    mapping = {
        # POS tags 
        # en: (Penn Treebank Project: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html)
        'NN'    : 'Noun',
        'NNS'   : 'Noun',
        'NNP'   : 'Noun',
        'NNPS'  : 'Noun',
        'PRP'   : 'Pronoun',
        'PRP$'  : 'Pronoun',
        'WP'    : 'Pronoun',
        'WP$'   : 'Pronoun',
    
        # pt: Universal POS Tags: http://universaldependencies.org/u/pos/
        #"ADJ": "adjective",
        #"ADP": "adposition",
        #"ADV": "adverb",
        #"AUX": "auxiliary",
        #"CONJ": "conjunction",
        #"CCONJ": "coordinating conjunction",
        #"DET": "determiner",
        #"INTJ": "interjection",
        "NOUN": "Noun",
        #"NUM": "numeral",
        #"PART": "particle",
        "PRON": "Pronoun",
        "PROPN": "Noun",
        #"PUNCT": "punctuation",
        #"SCONJ": "subordinating conjunction",
        #"SYM": "symbol",
        #"VERB": "verb",
        #"X": "other",
        #"EOL": "end of line",
        #"SPACE": "space",

        # NE labels
        'LOC'   : 'Loc',
        'ORG'   : 'Org',
        'PER'   : 'Per',
        'MISC'  : 'Other'    
    }

    return mapping.get(label, 'UNDEF')
