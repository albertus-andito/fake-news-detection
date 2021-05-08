# Knowledge-based Fake News Detection

This project is the implementation part of my undergraduate final year project, titled "Using Dynamic Knowledge Graph
for Fake News Detection". The final report is available to read in the [report.pdf](./report.pdf) file

This repository is hosted in [https://github.com/albertus-andito/fake-news-detection](https://github.com/albertus-andito/fake-news-detection).

The package documentation can be found at [/docs/_build/html/index.html](./docs/_build/html/index.html) or [/docs/fakenewsdetection.pdf](./docs/fakenewsdetection.pdf).

## File Listing
Below is a short explanation of the content of each directory and top-level file in this repository:
- [api](./api): Flask REST API
- [articlescraper](./articlescraper): article scrapers and RSS pollers
- [common](./common): common modules, such as Triple Producer and Knowledge Graph Wrapper
- [docs](./docs): python documentation of this package
- [evaluation-result](./evaluation-result): spreadsheet containing full evaluation result and usability testing result
- [factcheckers](./factcheckers): exact match and non-exact match fact-checkers
- [knowledgegraphupdater](./knowledgegraphupdater): Knowledge Graph Updater and its runner
- [ui](./ui): all things related to the User Interface
- [env.default](./env.default): default environment variables
- [definitions.py](./definitions.py): constants for logger
- [environment.yml](./environment.yml): Conda environment file containing list of external libraries
- [logger.conf](./logger.conf): logger config file
- [README.md](./README.md): project readme file
- [report.pdf](./report.pdf): final report (dissertation) of the project


## Prerequisites to Run
In order to run this project locally, you will need the followings:

1. Docker and Docker Compose.

    This is required for running DBpedia. If you do not already have Docker and Docker Compose, install it from 
   [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/) and 
   [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/).
   
2. A running DBpedia instance.

    Follow the instructions in [https://github.com/dbpedia/virtuoso-sparql-endpoint-quickstart](https://github.com/dbpedia/virtuoso-sparql-endpoint-quickstart) 
   to get DBpedia running locally. Note that it is not strictly required to have the full DBpedia loaded for 
   demonstration purpose, as it could take hours to load. Alternatively, use a smaller collection instead, as also 
   instructed in their documentation.

3. MongoDB

    This is required to store the scraped articles and their extracted triples. If you do not already have it, install 
   it from [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community).
   
4. Conda 
   
    This project uses Conda environment to manage Python and its packages. If you do not already have it, install
   Anaconda (including Conda) from [https://www.anaconda.com/products/individual](https://www.anaconda.com/products/individual).
   
5. Node.js

    This project uses Node.js for the User Interface. If you want to run the UI, you will need Node.js. If you do not
   already have it, install it from [https://nodejs.org/en/download/](https://nodejs.org/en/download/)
   
6. Stanford CoreNLP

    This is used for the triple extraction process. Download it from [https://stanfordnlp.github.io/CoreNLP/](https://stanfordnlp.github.io/CoreNLP/). 
   Java is required to run this.
   
7. (Optional) IIT OpenIE

    This can also be used for the triple extraction, as an alternative to Stanford OpenIE. Changes are required in the
   appropriate places in the code. Download it from 
   [https://github.com/dair-iitd/OpenIE-standalone](https://github.com/dair-iitd/OpenIE-standalone).
   
8. (Recommended) Guardian Open Platform API Key

    In order to smoothly scrape content from The Guardian, the Guardian API is used. Register for the developer key
   here: [https://bonobo.capi.gutools.co.uk/register/developer](https://bonobo.capi.gutools.co.uk/register/developer).

## Install The Project Locally

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
3. Create .env file by copying the content of .env.default file. Fill out all of the necessary values, or replace the 
   default ones.
   
4. Install the UI.
   Go to the ui folder (`cd ui`), and run the following commands: 
   ```
   npm install
   cp .\src\style\my-theme.less .\node_modules\antd\dist\
   cd .\node_modules\antd\dist\
   lessc --js my-theme.less ..\..\..\src\style\custom-antd.css
   ```

   
## Run The Project Locally

This project consists of 4 components that can be run individually.

### Run REST API
The REST API is needed to access the main functionalities of this project. It is also needed when running the UI.

1. Make sure that the local DBpedia and MongoDB are running.
2. Run the Stanford CoreNLP by using this command: (make sure you are running it from the directory where you have the
   Stanford CoreNLP jar file):
   ```
   java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
   -preload tokenize,ssplit,pos,lemma,depparse,natlog,openie \
   -port 9000 -timeout 15000
   ```
3. Run the REST API from the project root folder:
   ```
   conda activate fake-news-detection
   python -m api.main
   ```
4. You should now be able to hit the REST API endpoints on port 5000.
   You can also access the Swagger UI documentation and demo from [http://localhost:5000/apidocs/](http://localhost:5000/apidocs/).
   
### Run User Interface

The UI provides an intuitive way for users to interact with the REST API and the project as a whole.

1. Make sure the REST API is running.

2. Go to the ui folder (`cd ui`), and run the following command: `npm run start`.

3. The UI can be accessed through [http://localhost:3000](http://localhost:3000)

### Run Article Scraper in background

If you want to run the article scraper that runs periodically all the time, you need the followings:

1. Make sure MongoDB is running.
2. From the project's root directory, run `python -m articlescraper.main`

### Run Knowledge Graph Updater in background

If you want to have the triples extracted from the recently scraped articles all the time, you need the followings:

1. Make sure the Stanford CoreNLP server is running. See step 2 of Run REST API.
2. From the project's root directory, run `python -m knowledgegraphupdater.kgupdaterrunner`