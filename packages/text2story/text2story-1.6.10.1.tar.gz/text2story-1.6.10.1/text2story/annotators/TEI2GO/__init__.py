from text2story.core.exceptions import InvalidLanguage, UninstalledModel

try:
    import spacy
except ImportError:
    raise  ImportError("To use TEI2GO library, you should install spacy: pip install spacy")

pipeline = {}

def load(lang):
    """
    Used, at start, to load the pipeline for the supported languages.
    """
    if lang not in ["fr", "it", "de", "pt", "es", "en"]:
        raise InvalidLanguage(lang)

    try:
        pipeline[lang] = spacy.load(lang + "_tei2go")
    except OSError:
        model_name = lang + "_tei2go"
        command = f"pip install https://huggingface.co/hugosousa/{lang}_tei2go/resolve/main/{lang}_tei2go-any-py3-none-any.whl"
        raise UninstalledModel(model_name, command)

def extract_times(lang, text, publication_time=None):
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
        a list consisting of the times identified, where each time is represented by a tuple
        with the start and end character offset, it's value and type, respectively

    Raises
    ------
    InvalidLanguage if the language given is invalid/unsupported
    """
    if lang not in ["fr", "it", "de", "pt", "es", "en"]:
        raise InvalidLanguage(lang)

    timex_lst = pipeline[lang](text).ents

    ans = []
    for timex in timex_lst:

        start = timex.start_char
        end = timex.end_char
        label = timex.label_
        text = timex.text

        ans.append(((start, end), label, text))
    return ans