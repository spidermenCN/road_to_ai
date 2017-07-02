from __future__ import print_function
import os, codecs, math
import jieba

class BayesText:

    def __init__(self, trainingdir, stopwordlist, ignoreBucket):

        #trainingdir 训练集目录，子目录是分类，子目录中包含若干文本
        #stopwordlist 停用词列表（一行一个）
        #ignoreBucket 不纳入训练的目录

        self.vocabulary = {} #总词汇表
        self.prob = {} #每个分类下单词出现的次数
        self.totals = {}  #每个分类下单词的总数
        self.stopwords = {} #停用词
        f = open(stopwordlist)
        #f = codecs.open(stopwordlist, 'r', 'UTF-8')
        for line in f:
            self.stopwords[line.strip()] = 1
        f.close()
        categories = os.listdir(trainingdir)
        #将不是目录的元素过滤
        self.categories = [filename for filename in categories
                           if os.path.isdir(trainingdir + filename)]
        print("Counting ...")
        for category in self.categories:
            #print('    ' + category)
            (self.prob[category],
             self.totals[category]) = self.train(trainingdir, category,
                                                 ignoreBucket)
        # 删除出现次数小于3的单词
        toDelete = []
        for word in self.vocabulary:
            if self.vocabulary[word] < 3:
                # mark word for deletion
                # can't delete now because you can't delete
                # from a list you are currently iterating over
                toDelete.append(word)
        # 将词频数小于3的单词从词汇总表和各个分类中删除
        for word in toDelete:
            del self.vocabulary[word]
            for category in categories:
                if word in self.prob[category]:
                    del self.prob[category][word]
        # now compute probabilities
        vocabLength = len(self.vocabulary)
        #print("Computing probabilities:")
        for category in self.categories:
            #print('    ' + category)
            denominator = self.totals[category] + vocabLength
            for word in self.vocabulary:
                if word in self.prob[category]:
                    count = self.prob[category][word]
                else:
                    count = 1
                self.prob[category][word] = (float(count + 1)
                                             / denominator)
        #print ("DONE TRAINING\n\n")
                    

    def train(self, trainingdir, category, bucketNumberToIgnore):
        """counts word occurrences for a particular category"""
        ignore = "%i" % bucketNumberToIgnore
        currentdir = trainingdir + category
        directories = os.listdir(currentdir)
        counts = {}
        total = 0
        for directory in directories:
            if directory != ignore:
                currentBucket = trainingdir + category + "/" + directory
                files = os.listdir(currentBucket)
                #print("   " + currentBucket)
                for file in files:
                    f = codecs.open(currentBucket + '/' + file, 'r', 'iso8859-1')
                    #f = codecs.open(currentBucket + '/' + file, 'r', 'UTF-8')
                    for line in f:
                        tokens = line.split()
                        #tokens = jieba.cut(line, cut_all=False)
                        for token in tokens:
                            # get rid of punctuation and lowercase token
                            token = token.strip('\'".,?:-')
                            token = token.lower()
                            if token != '' and not token in self.stopwords:
                                self.vocabulary.setdefault(token, 0)
                                self.vocabulary[token] += 1
                                counts.setdefault(token, 0)
                                counts[token] += 1
                                total += 1
                    f.close()
        return(counts, total)
                    
                    
    def classify(self, filename):
        results = {}
        for category in self.categories:
            results[category] = 0
        f = codecs.open(filename, 'r', 'UTF-8')
        for line in f:
            tokens = line.split()
            #tokens = jieba.cut(line, cut_all=False)
            for token in tokens:
                #print(token)
                token = token.strip('\'".,?:-').lower()
                if token in self.vocabulary:
                    for category in self.categories:
                        if self.prob[category][token] == 0:
                            print("%s %s" % (category, token))
                        results[category] += math.log(
                            self.prob[category][token])
        f.close()
        results = list(results.items())
        results.sort(key=lambda tuple: tuple[1], reverse = True)
        # for debugging I can change this to give me the entire list
        return results[0][0]

    def testCategory(self, direc, category, bucketNumber):
        results = {}
        directory = direc + ("%i/" % bucketNumber)
        #print("Testing " + directory)
        files = os.listdir(directory)
        total = 0
        correct = 0
        for file in files:
            total += 1
            result = self.classify(directory + file)
            results.setdefault(result, 0)
            results[result] += 1
            #if result == category:
            #               correct += 1
        return results

    def test(self, testdir, bucketNumber):
        """Test all files in the test directory--that directory is
        organized into subdirectories--each subdir is a classification
        category"""
        results = {}
        categories = os.listdir(testdir)
        #filter out files that are not directories
        categories = [filename for filename in categories if
                      os.path.isdir(testdir + filename)]
        correct = 0
        total = 0
        for category in categories:
            #print(".", end="")
            results[category] = self.testCategory(
                testdir + category + '/', category, bucketNumber)
        return results

def tenfold(dataPrefix, stoplist):
    results = {}
    for i in range(0,10):
        bT = BayesText(dataPrefix, stoplist, i)
        r = bT.test(theDir, i)
        for (key, value) in r.items():
            results.setdefault(key, {})
            for (ckey, cvalue) in value.items():
                results[key].setdefault(ckey, 0)
                results[key][ckey] += cvalue
                categories = list(results.keys())
    categories.sort()
    print(   "\n       Classified as: ")
    header =    "          "
    subheader = "        +"
    for category in categories:
        header += "% 2s   " % category
        subheader += "-----+"
    print (header)
    print (subheader)
    total = 0.0
    correct = 0.0
    for category in categories:
        row = " %s    |" % category 
        for c2 in categories:
            if c2 in results[category]:
                count = results[category][c2]
            else:
                count = 0
            row += " %3i |" % count
            total += count
            if c2 == category:
                correct += count
        print(row)
    print(subheader)
    print("\n%5.3f percent correct" %((correct * 100) / total))
    print("total of %i instances" % total)

# change these to match your directory structure
prefixPath = "C:/Develop/data/"
theDir = prefixPath + "txt_sentoken/"
stoplistfile = prefixPath + "stopwords25.txt"

#计算准确率
tenfold(theDir, stoplistfile)

#bT = BayesText(theDir, stoplistfile, 10)
#判断文件内容属于什么分类
#print('classify: ' + bT.classify(''))

#计算某个词属于某个分类的概率


