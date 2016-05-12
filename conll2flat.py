import sys

def output(sents, outfile):
    fo = file(outfile,"w")
    for sent in sents:
        raw_sent = ' '.join(['[' + str(id) + ']' + info["token"] + '/' + info["pos"] for id, info in sent.items()])
        fo.write(raw_sent+"\n")
        rels = []
        for id, info in sent.items()[1:]:
            #:print info
            for rel in info["rel"]:
                rels.append('['+str(rel[0])+']'+sent[rel[0]]["token"]+'_['+str(id)+']'+info["token"]+'('+rel[1]+')')
        strs = " ".join(rels)
        fo.write(strs+"\n\n")
    
if __name__=="__main__":
    fi = file(sys.argv[1],"r")
    fi = fi.read()
    sents = fi.strip().split("\n\n")
    print "total sents: ",len(sents)
    sentences = []
    n = 0
    for sent in sents:
        sentences.append({})
        sentences[n][0] = {"token":"Root","pos":"Root","rel":[(-1, "-NULL-")]}
        lines = sent.strip().split("\n")
        for line in lines:
            items = line.strip().split("\t")
            if int(items[0]) not in sentences[n]:
                sentences[n][int(items[0])] = {"token":items[1],"pos":items[3],"rel":[(int(items[6]), items[7])]}
            else:
                sentences[n][int(items[0])]["rel"].append((int(items[6]), items[7]))
        n += 1
    output(sentences, sys.argv[2])

