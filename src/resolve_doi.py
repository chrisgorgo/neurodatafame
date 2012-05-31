import urllib2
from xml.etree import ElementTree
import datetime


def getPaperProperties(doi):
    xmlurl = 'http://doi.crossref.org/servlet/query'
    xmlpath = xmlurl + '?pid=k.j.gorgolewski@sms.ed.ac.uk&format=unixref&id=' + urllib2.quote(doi)
    xml_str = urllib2.urlopen(xmlpath).read()
    doc = ElementTree.fromstring(xml_str)
    if len(doc.getchildren()) == 0 or len(doc.findall('.//crossref/error')) > 0:
        raise Exception("DOI %s was not found" % doi)
    title = doc.findall('.//title')[0].text
    authors = [author.findall('given_name')[0].text + " " + author.findall('surname')[0].text for author in doc.findall('.//contributors/person_name')]
    if len(authors) > 1:
        authors = ", ".join(authors[:-1]) + " and " + authors[-1]
    url = doc.findall('.//doi_data/resource')[0].text
    date_node = doc.findall('.//publication_date')[0]
    if len(date_node.findall('day')) > 0:
        publication_date = datetime.date(int(date_node.findall('year')[0].text),
                                         int(date_node.findall('month')[0].text),
                                         int(date_node.findall('day')[0].text))
    elif len(date_node.findall('month')) > 0:
        publication_date = datetime.date(int(date_node.findall('year')[0].text),
                                         int(date_node.findall('month')[0].text),
                                         1)
    else:
        publication_date = datetime.date(int(date_node.findall('year')[0].text),
                                         1,
                                         1)
    return title, authors, url, publication_date

if __name__ == '__main__':
    print getPaperProperties('10.1016/j.neuroimage.2012.03.066')
    print getPaperProperties('10.1093/cercor/bhs139')
    print getPaperProperties('10.1007/s00234-012-1044-6')
    print getPaperProperties('10.1111/j.1552-6569.2012.00724.x')
    print getPaperProperties('10.3389/fninf.2012.00009')
    print getPaperProperties('10.3389/fninf.2012.0005509')
