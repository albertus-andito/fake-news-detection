import neuralcoref
import spacy

from utils import convert_to_dbpedia_resource


class EntityCorefResolver:
    """
    Entity Coreference Resolver (using Spacy and Neuralcoref)
    """
    BLACKLIST = ['i', 'me', 'my', 'mine',
                 'you', 'your', 'yours',
                 'he', 'him', 'his',
                 'she', 'her', 'hers',
                 'we', 'us', 'our', 'ours',
                 'they', 'them', 'their', 'theirs',
                 'it', 'its']

    def __init__(self):
        self.nlp = spacy.load('en')
        neuralcoref.add_to_pipe(self.nlp)

    def get_coref_clusters(self, doc):
        """
        Gets coreference clusters in DBpedia format.
        It returns a dictionary, where each key is the most representative mention for the cluster,
        and each value is a set of the other mentions for the cluster
        :param doc: a text
        :type doc: str
        :return: dictionary of coreference clusters, as described above
        :rtype: dict
        """
        spacy_doc = self.nlp(doc)
        coref_clusters = {convert_to_dbpedia_resource(cluster.main.text): {convert_to_dbpedia_resource(mention.text)
                                                                        for mention in cluster.mentions
                                                                        if mention.text.lower() not in self.BLACKLIST
                                                                        and mention.text != cluster.main.text}
                          for cluster in spacy_doc._.coref_clusters}
        coref_clusters = {main: mentions for main, mentions in coref_clusters.items() if len(mentions) > 0}
        return coref_clusters


import pprint

if __name__ == '__main__':
    coref_resolver = EntityCorefResolver()
    doc = "President Donald Trump's personal lawyer, Rudy Giuliani, has tested positive for Covid-19 and is being treated in hospital.  Mr Giuliani, who has led the Trump campaign's legal challenges to the election results, is the latest person close to the president to be infected.  Since November, he has been on a cross-country tour in an effort to convince state governments to overturn the vote. Like other Trump officials, he has been criticised for shunning face masks. Mr Trump, who was ill with the virus in October, announced the diagnosis in a tweet, writing: \"Get better soon Rudy, we will carry on!\" Mr Giuliani, 76, was admitted to the Medstar Georgetown University Hospital in Washington DC on Sunday. The news came after Mr Giuliani had visited Arizona, Georgia and Michigan all in the past week - where he spoke to government officials while not wearing masks. Following news of Mr Giuliani's diagnosis, the Arizona legislature announced sudden plans to shut down for one week. Several Republican lawmakers there had spent over 10 hours with the former New York mayor last week discussing election results.  Following Mr Giuliani's visit to Phoenix, Arizona, the state's Republican party tweeted a photo of him with other mask-less state lawmakers. In a tweet, Mr Giuliani thanked well-wishers for their messages, and said he was \"recovering quickly\".   His son, Andrew Giuliani, who works at the White House and tested positive for the virus last month, tweeted that his father was \"resting, getting great care and feeling well\".  It is not clear if Mr Giuliani is experiencing symptoms or when he caught the virus.  Nearly 14.6 million people have been infected with Covid-19 in the US, according to Johns Hopkins University, and 281,234 people have died - the highest figures of any country in the world. On Sunday, Dr Deborah Birx, the White House coronavirus task force co-ordinator, criticised the Trump administration for flouting guidelines and peddling \"myths\" about the pandemic.  \"I hear community members parroting back those situations, parroting back that masks don't work, parroting back that we should work towards herd immunity,\" Dr Birx told NBC. \"This is the worst event that this country will face,\" she said. Since the 3 November election, Mr Giuliani has travelled the country as part of unsuccessful efforts to overturn Mr Trump's election defeat. During many of his events, he was seen without a face mask and ignoring social distancing.  Last Wednesday, he appeared at a hearing on alleged election fraud in Michigan where he asked a witness beside him if she would be comfortable removing her face mask. \"I don't want you to do this if you feel uncomfortable, but would you be comfortable taking your mask off, so we can hear you more clearly?\" said Mr Giuliani, who was not wearing a face mask. The witness chose to keep her mask on after asking the panel if she could be heard. On Thursday Mr Giuliani travelled to Georgia where he repeated unsubstantiated claims of voter fraud at a Senate committee hearing about election security.  Dozens of people in Mr Trump's orbit are said to have tested positive for Covid-19 since October.  Boris Epshteyn, another Trump adviser, tested positive shortly after appearing alongside Rudy Giuliani at a news conference on 25 November. Others include the president's chief of staff Mark Meadows and press secretary Kayleigh McEnany, along with his wife Melania and sons Donald Jnr and Baron. Mr Trump's own diagnosis and hospital stay upended his campaign for a second term in office, less than a month before he faced Joe Biden in the presidential election. Mr Trump has refused to concede, insisting without evidence that the election was stolen or rigged. Attorney General William Barr said last week that his department had not seen any evidence of widespread voter fraud that would change the result. Mr Biden will be sworn in as president on 20 January."
    cluster = coref_resolver.get_coref_clusters(doc)
    pprint.pprint(cluster)

    doc = "Social distancing was neglected by Rudy Giuliani. He also claimed electoral fraud. Mr Giuliani studied sociology. He was admitted to hospital on Sunday."
    cluster = coref_resolver.get_coref_clusters(doc)
    pprint.pprint(cluster)
