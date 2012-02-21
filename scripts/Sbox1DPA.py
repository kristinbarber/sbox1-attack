import sys, itertools, math, operator, sqlite3, string
import scipy.stats

#################################
#######  Sbox1DPA Class #########
#################################
class Sbox1DPA:
    def __init__(self, keys, numTraces, outFile=None):
        self.keys = keys
        self.numTraces = numTraces
        self.possibleKeys = 2**6
        self.hammings = []
        self.simTraces = []
        self.peaks = {}
	self.conn = None
        self.cursor = None
        self.sbox1 = self.init_sbox1()

    def init_database(self):
	self.conn = sqlite3.connect('../db/database')
        self.cursor = self.conn.cursor()
        self.cursor.execute('DROP TABLE IF EXISTS hammings')
        self.cursor.execute('CREATE TABLE hammings(ptext1 INTEGER, ptext2 INTEGER, key1 INTEGER, key2 INTEGER, round INTEGER, hd1 INTEGER, hd2 INTEGER, combined INTEGER);')

    def close_database(self):
        self.conn.commit()
        self.conn.close()

    def binseq(self, k):
        lst = [int(''.join(x),2) for x in itertools.product('01', repeat=k)]
        return lst
    
    def hammingWeight(self, data):
        return bin(data).count('1')    

    def hammingDistance(self, d1, d2):
        return bin(d1 ^ d2)[2:].count('1')
    
    def init_sbox1(self):
        sbox1 = {0: [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0 ,7],
                 1: [0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8],
                 2: [4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0],
                 3: [15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13]}

        return sbox1

    def substitute(self, input):
        row = ( ( (input & 32) >> 4) | (input & 1) )
        column = input >> 1 & 15
        return self.sbox1[row][column] 

    def generatePowerSimulationModel(self, ptext):

        keys = self.binseq(6)
        d = {}

        for key in keys:
            input = ptext ^ key
            output = self.substitute(input)
            hd = self.hammingWeight(output)
            d[key] = hd

        self.hammings.append(d)
        
    def simulateModel(self, ptext):
        
        input = ptext ^ self.keys
        output = self.substitute(input)
        hd = self.hammingDistance(input, output)     
 
        self.simTraces.append(hd)
        
    def attack(self, measurements):
        xlist = []
        ylist = []
        correlations = {}

        for k in xrange(self.possibleKeys):
            for i in xrange(self.numTraces):
                xlist.append(self.hammings[i][k])
                ylist.append(measurements[i])
                    
            corr = scipy.stats.pearsonr(xlist, ylist)
            correlations[k] = corr[0]
            del xlist[:], ylist[:]
            
        return correlations    

    def findPeaks(self, dataFile):
        start = 24
        end = 28
	samples = []
	trace = dataFile.readline()

        for i in xrange(self.numTraces):

            if i%100 == 0 and i!=0: print 'Finding peak values for '+str(i)+'th encryption...'

            t2 = end*100
            t1 = start*100

       	    while trace != '':
                t = trace.split()
                if int(t[0]) >= t1 and int(t[0]) <= t2:
                    samples.append(Sample(int(t[0]), int(t[1])))
                elif int(t[0]) > t2:
                    break
                trace = dataFile.readline()

            peak = max(samples, key=operator.attrgetter('ampere'))
                
            self.peaks[i] = (peak.ampere)
                
            del samples[:]
            start = start + 10
            end = end + 10

        return self.peaks  

    def findKey( self, correlations ):
        lst = sorted(correlations.iteritems(), key=operator.itemgetter(1), reverse=True)
        return lst

    def generateMeasurementsFile(self, outFile):
        fout = open(outFile, 'w+')
	for ptext in self.peaks:
            fout.write(','.join(str(roundPeak) for roundPeak in self.peaks[ptext])+'\n')
        fout.close()
       
#######################################################################

#################################
#######  Sample Class  ##########
#################################
class Sample:
    def __init__(self, time, ampere):
        self.time = time
        self.ampere = ampere
        self.correlationValue = 0
