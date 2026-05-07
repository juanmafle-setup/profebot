import spacy

nlp = spacy.load("es_core_news_sm")

def procesar(texto):
    doc = nlp(texto)
    entidades = [(ent.text, ent.label_) for ent in doc.ents]

    return {"entidades": entidades}