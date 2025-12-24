"""
    LUSA annotator

    Used for:
        - Event extraction
            'en' : https://huggingface.co/evelinamorim/bert-lusa-eventype-classifier)
"""

from text2story.core.exceptions import InvalidLanguage

from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import torch.nn.functional as F

pipeline = {}


def load(lang):
    """
    Used, at start, to load the pipeline for the supported languages.
    """
    if lang == "en":
        model_name = "evelinamorim/bert-lusa-eventype-classifier"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        pipeline['en'] = {'model':None,
                          'tokenize':None}
        pipeline['en']['model'] = AutoModelForTokenClassification.from_pretrained(model_name)
        pipeline['en']['tokenizer'] = AutoTokenizer.from_pretrained(model_name)
    else:
        raise InvalidLanguage(lang)


def extract_events(lang, text):
    """
    Parameters
    ----------
    lang : str
        the language of text to be annotated
    text : str
        the text to be annotated

    Returns
    -------
    list[tuple[tuple[int, int], Dict[str,str]]]
        the list of events identified where each event is represented by its offset (tuple), and a dictionary of attributes

    Raises
    ------
        InvalidLanguage if the language given is invalid/unsupported
    """

    if lang not in ['en']:
        raise InvalidLanguage(lang)

    inputs = pipeline['en']['tokenizer'](text,
                                         return_tensors="pt",
                                         truncation=True,
                                         max_length=512,
                                         return_offsets_mapping=True
                                         )

    offset_mapping = inputs.pop("offset_mapping")[0].tolist()
    # Predict
    with torch.no_grad():
        outputs = pipeline['en']['model'](**inputs)
        probabilities = F.softmax(outputs.logits, dim=2)
        confidences, predictions = torch.max(probabilities, dim=2)

    # Decode predictions
    predictions = predictions[0]  # Shape: (sequence_length,)
    confidences = confidences[0]  # Shape: (sequence_length,)

    predicted_labels = [pipeline['en']['model'].config.id2label[p.item()] for p in predictions]

    # Set confidence threshold
    CONFIDENCE_THRESHOLD = 0.5  # Adjust this value as needed

    # Group consecutive tokens into events
    event_list = []
    current_event = None
    current_type = None
    current_start = None
    current_end = None
    confidences_list = []

    for idx, (label, confidence, (start, end)) in enumerate(zip(predicted_labels, confidences, offset_mapping)):
        # Skip special tokens (they have offset (0, 0) except the first CLS token)
        if start == end:
            continue

        if label.startswith("B-"):
            # Save previous event if exists
            if current_event is not None and confidences_list:
                avg_confidence = sum(confidences_list) / len(confidences_list)
                if avg_confidence >= CONFIDENCE_THRESHOLD:
                    event_list.append(((current_start, current_end), {"Type": current_type}))

            # Start new event
            event_type = label[2:]  # Remove "B-" prefix
            current_event = text[start:end]
            current_type = event_type
            current_start = start
            current_end = end
            confidences_list = [confidence.item()]

        elif label.startswith("I-"):
            # Continue current event
            event_type = label[2:]  # Remove "I-" prefix
            if current_event is not None and event_type == current_type:
                current_event += text[current_end:end]
                current_end = end
                confidences_list.append(confidence.item())
            else:
                # Mismatched I- tag, start new event
                if current_event is not None and confidences_list:
                    avg_confidence = sum(confidences_list) / len(confidences_list)
                    if avg_confidence >= CONFIDENCE_THRESHOLD:
                        event_list.append(((current_start, current_end), {"Type": current_type}))

                current_event = text[start:end]
                current_type = event_type
                current_start = start
                current_end = end
                confidences_list = [confidence.item()]
        else:
            # "O" label - save previous event if exists
            if current_event is not None and confidences_list:
                avg_confidence = sum(confidences_list) / len(confidences_list)
                if avg_confidence >= CONFIDENCE_THRESHOLD:
                    event_list.append(((current_start, current_end), {"Type": current_type}))

            current_event = None
            current_type = None
            confidences_list = []

    # Don't forget the last event
    if current_event is not None and confidences_list:
        avg_confidence = sum(confidences_list) / len(confidences_list)
        if avg_confidence >= CONFIDENCE_THRESHOLD:
            event_list.append(((current_start, current_end), {"Type": current_type}))

    return event_list


