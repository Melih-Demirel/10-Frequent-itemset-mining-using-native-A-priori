import xml.sax
import time
import itertools
import sys

tags = ["article", "incollection", "book", "proceedings", "inproceedings", "phdthesis", "mastersthesis"]
triggerTags = ["author"] # We could also add the tag "editor" here if we want.  

class DblpHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.author = ""
        self.authorsOfBasket = []
    def startElement(self, name, attrs):
        self.readContent = True if name in triggerTags else False
        if name in tags:
            self.authorsOfBasket = []

    def endElement(self, name):
        self.readContent = False
        if name in triggerTags:
            if self.author:
                self.authorsOfBasket.append(self.author)
        if name in tags:
            if self.authorsOfBasket:
                f = frozenset(self.authorsOfBasket)
                for au in f:
                    if au in candidatesSupport:
                        candidatesSupport[au] += 1
                    else:
                        candidatesSupport[au] = 1
                baskets.append(f)
        self.author = ""

    def characters(self, content):
        if self.readContent:
            self.author += content

def writeXMLtoTXT():
    """
    Write read XML data to TXT file. 
    Handy when we have big xml containing useless information. 
    So for next steps, we just read the TXT.
    """
    with open(AUTHORS_FILE, "w") as f:
        for basket in baskets:
            f.write(";".join(basket) + "\n")

def parseXml():
    """
    Parsing XML file using SAX parser.
    """
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    handler = DblpHandler()
    parser.setContentHandler(handler)
    parser.parse(XML_FILE)

def readTXT(file):
    """
    Reads TXT file which respresent the baskets, each line containing a basket.
    While reading baskets, we also count the support of the authors.
    """
    with open(file, "r") as f:
        for line in f:
            basket = line.strip('\n').split(";")
            for au in basket:
                if au in candidatesSupport:
                    candidatesSupport[au] += 1
                else:
                    candidatesSupport[au] = 1
            baskets.append(frozenset(basket))
    #debug()

def debug():
    """
    Checks wether XML is read like we wanted by comparing it with data from the website.
    """
    top_5_authors = sorted(candidatesSupport.items(), key=lambda item: item[1], reverse=True)[:5]
    print(top_5_authors)
    print(f"Count Brecht Vandevoort: {candidatesSupport.get('Brecht Vandevoort')} / 14 (15 with editorship)")
    print(f"Count Frank Neven: {candidatesSupport.get('Frank Neven')} / 147 (150 with editorship)")
    print(f"Count Frank Niels Bylois: {candidatesSupport.get('Niels Bylois')} / 2")
    print(f"Count Frank Stijn Vansummeren: {candidatesSupport.get('Stijn Vansummeren')} / 100 (102 with editorship)")
    print(f"Count Yu Zhang: {candidatesSupport.get('Yu Zhang')} / 1865 (1870 with editorship)")
    print(f"Count Dilay Çelebi: {candidatesSupport.get('Dilay Çelebi')} / 9")
    
    print(f"Count baskets: {len(baskets)}")
    largest_basket = max(baskets, key=lambda basket: len(basket))
    print(f"Largest basket: {len(largest_basket)}")

def outputInformationForEachGroupSize(groupData):
    k, max_count, authors, threshold = groupData
    authorsStr = ', '.join(str(i) for i in authors)
    print(f"{k:14} | {threshold:14} | {max_count:19} | {authorsStr}")

def outputDebugInformation():
    print(f"C{k}:")
    for candidate, support in candidatesSupport.items():
        print(candidate, ":", support)
    print()
    print(f"L{k}:")
    for freqCandidate in freqCandidates:
        print(freqCandidate)
    print()

def isValidCandidate(possibleCandidate):
    """
    Pruning method: for a given possible candidate, it checks wether is subsets are frequent.
    Example: 
        FreqItems:  (1,2), (2,3), (3,4), (2,4)
        invalid :   (1,2,3) -> 1,3 is not frequent.
        valid:      (2,3,4) -> all subsets: (2,3), (3,4), (2,4) are frequent.
    """
    isValidCand = True
    subsets = []
    for comb in itertools.combinations(possibleCandidate, len(possibleCandidate) - 1):
        if len(comb) == 1:
            # When comb = [('1',)], it has an extra "," in the end which needs to be removed.
            subsets.append(comb[0])
        else:
            subsets.append(comb)
    for sub in subsets:
        subset = set(sub)
        found = False
        for my_tuple in freqCandidates:
            if subset.issubset(set(my_tuple)):
                found = True
                break  # Exit the inner loop early -> subset frequent, keep checking.

        if not found:
            isValidCand = False
            break  # Exit the outer loop early -> subset was not frequent so no need to keep checking.
    return isValidCand

def changeThresholdDynamic(percentage, threshold):
    """
    Given a percentage (ex. 25), it will try to reach for a threshold where around 25% or less than 25% of the candidates are frequent candidates.
    """
    decimal_p = percentage / 100
    while True:
        freqCandidates = {author[0] for author in filter(lambda author: author[1] >= threshold, candidatesSupport.items())}
        if len(candidatesSupport) * decimal_p < len(freqCandidates):
            break
        else:
            threshold-= 1
            if threshold == 1:
                break
        if not freqCandidates:
            break
    return threshold

if __name__ == "__main__":

    # Default File names, useful when no arguments are given. (3rd way of program)
    XML_FILE = "dblpR.xml"
    AUTHORS_FILE = "exampleFromCoursePdf.txt"

    baskets = [] # We dont use a set here because cant have duplicates in sets. Example: We might have 2 articles with same authorsOfBasket)
    candidatesSupport = {}

    """
        Program has 3 ways to run:
        - TO_READ_XML_FILENAME , TO_WRITE_TXT_FILENAME : 
            Will read XML FILE for 1 time and write its data to a TXT file. Algorithm wont run here.
            Example: python3 main.py dblp.xml authors.txt
        - TO_READ_TXT_FILENAME:
            Will fetch all data from TXT file for algorithm.
            Example: python3 main.py authors.txt
        - no arg:
            Will run algorithm on an example we have seen in the course.
    """
    if len(sys.argv) == 3:
        XML_FILE = sys.argv[1]
        AUTHORS_FILE = sys.argv[2]
        parseXml()                  # Does +- 150 secs over full DBLP dataset.
        writeXMLtoTXT()
        exit()
    elif len(sys.argv) == 2:
        AUTHORS_FILE = sys.argv[1]
        readTXT(AUTHORS_FILE)       # Does +- 25 secs over full DBLP dataset.
    else:
        readTXT(AUTHORS_FILE)

    # If true: DEBUG PURPOSE, will output candidates of each k step. BUT WONT SHOW MAX FREQUENT ITEMSET OF EACH K WHEN TRUE.
    printDebugInformation = False
    # Timer to see how long it takes for a certain threshold.
    start = time.time()
    # First step obviously 
    k = 1
    # Options to use dynamic threshold, which will change depending on the candidate itemsets.
    enableDynamicThreshold = True
    
    

    print()
    if enableDynamicThreshold:
        threshold = max(candidatesSupport.values())
        # For big datasets, take a small number so not everything goes through step 1.
        # For small datasets, you need a very big number in order to get everything through step one.
        firstStepPercentageFrequentIWant = 20
        # For each k step, how many of those candidates we want to let through k+1
        # Like said before, choose HIGH if len(candidates) is low or LOW when len(candidates) is high
        kStepPercentageFrequentIWant = 5
        threshold = changeThresholdDynamic(firstStepPercentageFrequentIWant, threshold)
        print(f"Dynamic Threshold enabled:")
        print(f"{firstStepPercentageFrequentIWant}% of singles will go to L2.")
        print(f"{kStepPercentageFrequentIWant}% of k size itemsets will go to L(k+1).")
    else:
        threshold = 10
        print(f"Static Threshold enabled: {threshold}")

    freqCandidates = {author[0] for author in filter(lambda author: author[1] >= threshold, candidatesSupport.items())}

    if printDebugInformation:
        outputDebugInformation()
    else:
        # HEADER FOR OUTPUT
        title = "Group Size (k) | Used Threshold | Max Frequency Count | Example Author Groups"
        print()
        print("-" * len(title))
        print(title)
        print("-" * len(title))
        ###################
        max_count = max(candidatesSupport.values())
        max_authors = [author for author, count in candidatesSupport.items() if count == max_count]
        outputInformationForEachGroupSize([k, max_count, max_authors, threshold])
    k+=1

    
    while freqCandidates:
        candidates = []
        candidatesSupport = {}
        for basket in baskets:
            for combination in list(itertools.combinations(basket, k)):
                combination = sorted(combination) # We sort so A,B is the same as B,A
                if tuple(combination) in candidatesSupport:
                    candidatesSupport[tuple(combination)] += 1
                if combination not in candidates and isValidCandidate(combination):
                    candidates.append(combination)
                    candidatesSupport[tuple(combination)] = 1

        # Change treshold if dynamic, else no change need because its a static threshold.
        if enableDynamicThreshold:
            threshold = changeThresholdDynamic(kStepPercentageFrequentIWant, threshold)

        freqCandidates = {author[0] for author in filter(lambda author: author[1] >= threshold, candidatesSupport.items())}

        if printDebugInformation:
            outputDebugInformation()
        else:
            if candidatesSupport:
                max_count = max(candidatesSupport.values())
                max_authors = [author for author, count in candidatesSupport.items() if count == max_count]
                outputInformationForEachGroupSize([k, max_count, max_authors, threshold])
        k += 1
        
    print()
    end = time.time()
    print(f"This took: {end-start} seconds.")