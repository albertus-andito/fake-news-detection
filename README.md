# fake-news-detection

### Install NeuralCoref for spacy > 2.1.0
```
git clone https://github.com/huggingface/neuralcoref.git
cd neuralcoref
pip install -r requirements.txt
pip install -e .
```

### Run StanfordCoreNLP
```
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
-preload tokenize,ssplit,pos,lemma,depparse,natlog,openie \
-port 9000 -timeout 15000
```