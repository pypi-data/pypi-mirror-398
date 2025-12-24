import re
from typing import Optional, Tuple

from ovos_bus_client.session import Session, SessionManager
from ovos_number_parser import pronounce_number
from ovos_plugin_manager.templates.transformers import DialogTransformer
from ovos_utils.log import LOG
from unicode_rbnf import RbnfEngine, FormatPurpose


class DialogNormalizerTransformer(DialogTransformer):
    """OVOS Dialog Transformer plugin to normalize text for TTS engines:
    - Expands digits into words
    - Handles common abbreviations
    - Supports multiple languages
    """
    CONTRACTIONS = {
        "en": {
            "I'd": "I would",
            "I'll": "I will",
            "I'm": "I am",
            "I've": "I have",
            "ain't": "is not",
            "aren't": "are not",
            "can't": "can not",
            "could've": "could have",
            "couldn't": "could not",
            "didn't": "did not",
            "doesn't": "does not",
            "don't": "do not",
            "gonna": "going to",
            "gotta": "got to",
            "hadn't": "had not",
            "hasn't": "has not",
            "haven't": "have not",
            "he'd": "he would",
            "he'll": "he will",
            "he's": "he is",
            "how'd": "how did",
            "how'll": "how will",
            "how's": "how is",
            "isn't": "is not",
            "it'd": "it would",
            "it'll": "it will",
            "it's": "it is",
            "might've": "might have",
            "mightn't": "might not",
            "must've": "must have",
            "mustn't": "must not",
            "needn't": "need not",
            "oughtn't": "ought not",
            "shan't": "shall not",
            "she'd": "she would",
            "she'll": "she will",
            "she's": "she is",
            "should've": "should have",
            "shouldn't": "should not",
            "somebody's": "somebody is",
            "someone'd": "someone would",
            "someone'll": "someone will",
            "someone's": "someone is",
            "that'd": "that would",
            "that'll": "that will",
            "that's": "that is",
            "there'd": "there would",
            "there're": "there are",
            "there's": "there is",
            "they'd": "they would",
            "they'll": "they will",
            "they're": "they are",
            "they've": "they have",
            "wasn't": "was not",
            "we'd": "we would",
            "we'll": "we will",
            "we're": "we are",
            "we've": "we have",
            "weren't": "were not",
            "what'd": "what did",
            "what'll": "what will",
            "what're": "what are",
            "what's": "what is",
            "what've": "what have",
            "whats": "what is",
            "when'd": "when did",
            "when's": "when is",
            "where'd": "where did",
            "where's": "where is",
            "where've": "where have",
            "who'd": "who would",
            "who'd've": "who would have",
            "who'll": "who will",
            "who're": "who are",
            "who's": "who is",
            "who've": "who have",
            "why'd": "why did",
            "why're": "why are",
            "why's": "why is",
            "won't": "will not",
            "won't've": "will not have",
            "would've": "would have",
            "wouldn't": "would not",
            "wouldn't've": "would not have",
            "y'ain't": "you are not",
            "y'aint": "you are not",
            "y'all": "you all",
            "ya'll": "you all",
            "you'd": "you would",
            "you'd've": "you would have",
            "you'll": "you will",
            "you're": "you are",
            "you've": "you have",
            "I'm'a": "I am going to",
            "I'm'o": "I am going to",
            "I'll've": "I will have",
            "I'd've": "I would have",
            "Whatcha": "What are you",
            "amn't": "am not",
            "'cause": "because",
            "can't've": "cannot have",
            "couldn't've": "could not have",
            "daren't": "dare not",
            "daresn't": "dare not",
            "dasn't": "dare not",
            "everyone's": "everyone is",
            "gimme": "give me",
            "gon't": "go not",
            "hadn't've": "had not have",
            "he've": "he would have",
            "he'll've": "he will have",
            "he'd've": "he would have",
            "here's": "here is",
            "how're": "how are",
            "how'd'y": "how do you do",
            "howd'y": "how do you do",
            "howdy": "how do you do",
            "'tis": "it is",
            "'twas": "it was",
            "it'll've": "it will have",
            "it'd've": "it would have",
            "kinda": "kind of",
            "let's": "let us",
            "ma'am": "madam",
            "may've": "may have",
            "mayn't": "may not",
            "mightn't've": "might not have",
            "mustn't've": "must not have",
            "needn't've": "need not have",
            "ol'": "old",
            "oughtn't've": "ought not have",
            "sha'n't": "shall not",
            "shan't": "shall not",
            "shalln't": "shall not",
            "shan't've": "shall not have",
            "she'd've": "she would have",
            "shouldn't've": "should not have",
            "so've": "so have",
            "so's": "so is",
            "something's": "something is",
            "that're": "that are",
            "that'd've": "that would have",
            "there'll": "there will",
            "there'd've": "there would have",
            "these're": "these are",
            "they'll've": "they will have",
            "they'd've": "they would have",
            "this's": "this is",
            "this'll": "this will",
            "this'd": "this would",
            "those're": "those are",
            "to've": "to have",
            "wanna": "want to",
            "we'll've": "we will have",
            "we'd've": "we would have",
            "what'll've": "what will have",
            "when've": "when have",
            "where're": "where are",
            "which's": "which is",
            "who'll've": "who will have",
            "why've": "why have",
            "will've": "will have",
            "y'all're": "you all are",
            "y'all've": "you all have",
            "y'all'd": "you all would",
            "y'all'd've": "you all would have",
            "you'll've": "you will have"
        }
    }

    TITLES = {
        "en": {
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Prof.": "Professor"
        },
        "ca": {
            "Dr.": "Doctor",
            "Sr.": "Senyor",
            "Sra.": "Senyora",
            "Prof.": "Professor"
        },
        "es": {
            "Dr.": "Doctor",
            "Sr.": "Señor",
            "Sra.": "Señora",
            "Prof.": "Profesor",
            "D.": "Don",
            "Dña.": "Doña"
        },
        "pt": {
            "Dr.": "Doutor",
            "Sr.": "Senhor",
            "Sra.": "Senhora",
            "Prof.": "Professor",
            "Drª.": "Doutora",
            "Eng.": "Engenheiro",
            "D.": "Dom",
            "Dª": "Dona"
        },
        "gl": {
            "Dr.": "Doutor",
            "Sr.": "Señor",
            "Sra.": "Señora",
            "Prof.": "Profesor",
            "Srta.": "Señorita"
        },
        "fr": {
            "Dr.": "Docteur",
            "M.": "Monsieur",
            "Mme": "Madame",
            "Mlle": "Mademoiselle",
            "Prof.": "Professeur",
            "Pr.": "Professeur"
        },
        "it": {
            "Dr.": "Dottore",
            "Sig.": "Signore",
            "Sig.ra": "Signora",
            "Prof.": "Professore",
            "Dott.ssa": "Dottoressa",
            "Sig.na": "Signorina"
        },
        "nl": {
            "Dr.": "Dokter",
            "Dhr.": "De Heer",
            "Mevr.": "Mevrouw",
            "Prof.": "Professor",
            "Drs.": "Dokterandus",
            "Ing.": "Ingenieur"
        },
        "de": {
            "Dr.": "Doktor",
            "Prof.": "Professor"
        }
    }

    def __init__(self, name="ovos-dialog-normalizer-plugin", priority=5, config=None):
        super().__init__(name=name, priority=priority, config=config)

    def transform(self, dialog: str, context: Optional[dict] = None) -> Tuple[str, dict]:
        """Normalize dialog text."""
        context = context or {}
        sess = Session.deserialize(context["session"]) if "session" in context else SessionManager.get()
        lang = sess.lang.split("-")[0]

        original = dialog
        try:
            rbnf_engine = RbnfEngine.for_language(lang)
        except:  # doesnt support lang
            rbnf_engine = None

        # substitute ' €' by 'euros' and 'someword€' by 'someword euros'
        dialog = re.sub(r"(\w+)\s*€", r"\1 euros", dialog)

        try:
            # TODO - add language specific code here if needed
            if lang == "gl":
                # substitute ' ºC' by 'graos centígrados' and 'somewordºC' by 'someword graos centígrados'
                dialog = re.sub(r"(\w+)\s*ºC", r"\1 graos centígrados", dialog)

            words = dialog.split()
            for idx, word in enumerate(words):

                if word in self.CONTRACTIONS.get(lang, {}):
                    words[idx] = self.CONTRACTIONS[lang][word]
                    continue

                if word in self.TITLES.get(lang, {}):
                    words[idx] = self.TITLES[lang][word]
                    continue

                if word.isdigit():
                    try:
                        words[idx] = pronounce_number(int(word), lang=sess.lang)
                    except Exception as e:
                        LOG.error(f"ovos-number-parser failed to pronounce number: {word} - ({e})")

                # NOTE: pronounce_digit may return the digit itself again for some languages (upstream bug)
                # we recheck if isdigit() to handle this
                if rbnf_engine and words[idx].isdigit():
                    # fallback to unicode RBNF
                    try:
                        words[idx] = rbnf_engine.format_number(word, FormatPurpose.CARDINAL).text
                    except Exception as e:
                        LOG.error(f"unicode-rbnf failed to pronounce number: {word} - ({e})")

            dialog = " ".join(words)

            LOG.debug(f"normalized dialog: '{original}' -> '{dialog}'")
        except Exception as e:
            LOG.error(f"Failed to normalize dialog: {e}")

        return dialog, context


if __name__ == "__main__":
    # Silly example for demonstration purposes
    # 'I am Doctor Professor twelve thousand three hundred forty-five'
    print(DialogNormalizerTransformer().transform("I'm Dr. Prof. 12345 €"))
