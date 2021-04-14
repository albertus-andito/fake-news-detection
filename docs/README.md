# Knowledge-based Fake News Detection

This project is the implementation part of my undergraduate final year project, titled "Using Dynamic Knowledge Graph
for Fake News Detection". The final report will be available to read here once it is done and submitted.

# Prerequisites to Run
In order to run this project locally, you will need the followings:

1. Docker and Docker Compose.

    This is required for running DBpedia. If you do not already have Docker and Docker Compose, install it from 
   https://docs.docker.com/engine/install/ and https://docs.docker.com/compose/install/.
   
2. A running DBpedia instance.

    Follow the instructions in https://github.com/dbpedia/virtuoso-sparql-endpoint-quickstart to get DBpedia running 
   locally. Note that it is not strictly required to have the full DBpedia loaded for demonstration purpose, as it could
   take hours to load. Alternatively, use a smaller collection instead, as also instructed in their documentation.

3. MongoDB

    This is required to store the scraped articles and their extracted triples. If you do not already have it, install 
   it from https://www.mongodb.com/try/download/community.
   
4. Conda 
   
    This project uses Conda environment to manage Python and its packages. If you do not already have it, install
   Anaconda (including Conda) from https://www.anaconda.com/products/individual.
   
5. Node.js

    This project uses Node.js for the User Interface. If you want to run the UI, you will need Node.js. If you do not
   already have it, install it from https://nodejs.org/en/download/
   
6. Stanford CoreNLP

    This is used for the triple extraction process. Download it from https://stanfordnlp.github.io/CoreNLP/. Java is 
   required to run this.
   
# Install The Project Locally

1. From the terminal, run:
   ```
   conda env create --file environment.yml
   ```

2. Once the Conda environment is installed, additionally you will need to install NeuralCoref library which needs to be
built locally because the Spacy version used in this project is later than version 2.1.0.
   
    Run the following commands:
   ```
   git clone https://github.com/huggingface/neuralcoref.git
   cd neuralcoref
   pip install -r requirements.txt
   pip install -e .
   ```

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