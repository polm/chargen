import fileinput, json, codecs, sys
source =''
for line in fileinput.input():
    source += line.strip() + ' '

writer = codecs.getwriter('utf8')
sys.stdout = writer(sys.stdout)

data = json.loads(source)
for key in data:
    print ";" + key
    for val in sorted(data[key]):
        print "1," + val
    print ""


