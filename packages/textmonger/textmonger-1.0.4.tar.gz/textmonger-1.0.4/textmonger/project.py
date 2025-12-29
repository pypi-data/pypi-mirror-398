import csv
import spacy
from textmonger.power import Power
from spacy import displacy
from spacy.cli import download
from pyfiglet import Figlet
from textmonger.readability import Readability
from textblob import TextBlob

def main():
    print(ascii('The Text Monger'))
    
    text = get_lines()

    print("\n" + "="*80)
    print(f"{' ' * 30}Readability Analysis")
    print("="*80)
    
    analysis = Readability(text)
    print(analysis.analyze())

    print("\n" + "="*80)
    print(f"{' ' * 30}Power Words Distribution")
    print("="*80)
    
    strong = Power('power_words.csv', text)
    cat_count = strong.find()
    ascii_chart = strong.ascii_pie_chart(cat_count)
    print('\n' + ascii_chart)
    
    print("\n" + "="*80)
    print(f"{' ' * 30}Sentiment Analysis")
    print("="*80)
    
    sentiment_analysis(text)

    print("\n" + "="*80)
    print(f"{' ' * 30}Named Entity Recognition (NER)")
    print("="*80)
    
    ner(text)

def ascii(text):
    f = Figlet()
    return f.renderText(text)

def get_lines():
    print("Enter Text to analyze (type 'END' on a new line to finish):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        lines.append(line)
    text = "\n".join(lines)
    return text

def load_spacy_model(model_name):
    try:
        nlp = spacy.load(model_name)
    except OSError:
        print(f"Model '{model_name}' not found. Downloading it now...")
        download(model_name)
        nlp = spacy.load(model_name)
    return nlp

def ner(text):
    nlp = load_spacy_model('en_core_web_sm')
    doc = nlp(text)
    displacy.serve(doc, style='ent', auto_select_port=True)

def sentiment_analysis(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment
    print(f"Sentiment Polarity: {sentiment.polarity:.2f}")
    print(f"Sentiment Subjectivity: {sentiment.subjectivity:.2f}")

if __name__ == "__main__":
    main()
