import requests
from elasticsearch import Elasticsearch, helpers


def findPublications(idHal, field, increment=0):

    articles = []
    flags = 'docid,halId_s,title_s,*_keyword_s,*_abstract_s,authEmailDomain_s,authFullName_s,authIdHal_s,authStructId_i,city_s,authOrganism_s,collCategory_s,collName_s,coordinates_s,country_s,deptStructAcronym_s,deptStructCountry_s' \
            'domainAllCode_s,domain_s,doiId_s,fileMain_s,fulltext_t,instStructCountry_s,instStructName_s,instStructAcronym_s,journalPublisher_s,journalSherpaColor_s,journalTitle_s,labStructAcronym_s,labStructCountry_s,location,' \
            'openAccess_bool,modifiedDate_tdate,primaryDomain_s,producedDate_tdate,publicationDate_tdate,publisher_s,publicationLocation_s,rgrpInstStructAcronym_s,rgrpLabStructAcronym_s,scientificEditor_s,structAcronym_s,structCountry_s,structId_i,' \
            'structName_t,submittedDate_tdate,licence_t'

    req = requests.get('http://api.archives-ouvertes.fr/search/?q=' + field + ':' + str(idHal) + '&fl=' + flags + '&start=' + str(increment))

    if req.status_code == 200:
        data = req.json()
        if "response" in data.keys():
            data = data['response']
            count = data['numFound']

            req = requests.get('http://api.archives-ouvertes.fr/search/?q=' + field + ':' + str(idHal) + '&fl=' + flags + '&start=' + str(increment))
            data = req.json()
            if "response" in data.keys():
                data = data['response']
                count = data['numFound']

            for article in data['docs']:

                try:
                    article['country_s'] = article['country_s'].upper()
                except:
                    pass
                try:
                    article['instStructCountry_s'] = article['instStructCountry_s'].upper()
                except:
                    pass
                try:
                    article['labStructCountry_s'] = article['labStructCountry_s'].upper()
                except:
                    pass
                try:
                    article['deptStructCountry_s'] = article['deptStructCountry_s'].upper()
                except:
                    pass
                try:
                    article['structCountry_s'] = article['structCountry_s'].upper()
                except:
                    pass

                articles.append(article)

            upload = False
            if upload:
                es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

                res = helpers.bulk(
                    es,
                    articles,
                    index="hal-utln",
                )

            if (count > 30) and (increment < (count)):
                increment += 30
                tmp_articles = findPublications(idHal, field, increment=increment)
                for tmp_article in tmp_articles:
                    articles.append(tmp_article)

                return articles
            else:
                return articles
        else:
            print('Error : wrong response from HAL API endpoint')
            return -1
    else:
        print('Error : can not reach HAL API endpoint')
        return articles


publications = findPublications(303091, 'structId_i')