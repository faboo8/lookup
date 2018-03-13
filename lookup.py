# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 16:01:10 2018

@author: Fabian Hafner
"""

# In[ ]:


import requests
import re
import itertools
import zeep
import zeep.helpers
from abc import ABC, abstractmethod
from zeep.exceptions import ValidationError
import argparse
import pandas as pd
from zeep.cache import SqliteCache
from zeep.transports import Transport



#DE194821795
#ATU33864707
global transport
transport = Transport(cache=SqliteCache)


class AbstractLookupStrategy(ABC):
    def __init__(self, uid, uid_tn = '', comp_name = '', comp_type='', city= '', plz = '', street= ''):
        while True:
            try:
                value = {'uid': uid,  'uid_tn': uid_tn, 
                     'comp_name': comp_name,  'comp_type': comp_type,
                     'city':city, 'zip': plz, 'street': street}
                self.value = value
                break
            except:
                raise ValueError('Invalid number of input arguments')
        
        super(AbstractLookupStrategy, self).__init__()
        
    @staticmethod
    @abstractmethod
    def get_info():
        print('This should be overridden')
            
    @abstractmethod
    def SendRequest(self):
        pass
    
    
"""
Input:    value = {  'zu prüdende id': '123', 'eigene id': '456',
                   'firmenname': 'pwc', 'firnmenart':'gmbh','ort': 'Berlin', 'plz':'123456',  
                   'strasse': 'beispielstraße'}    +  login credentials for finanzonline
"""



class FinanzonlineLookupStrategy(AbstractLookupStrategy):
    @staticmethod
    def get_info():
            print("""
                  Class to send a request to Finannzonline VAT Lookup Service
                  
                  Needed input: foreign VAT
                  
                  Return: validity, adress, company name
                  """)
    def SendRequest(self):
         
        SESSION_KEYS={'tid':'wt803271g', 'benid' : 'test123456',
                      'pin' : 'start01pwc', 'herstellerid': 'ATU66127899'} 

        LOGIN_KEYS = {'tid':'wt803271g', 'benid' : 'test123456',
                      'id' : '', 'uid_tn': 'ATU66127899' ,'uid': self.value['uid'], 'stufe':'2'}

        SESSION_URL = 'https://finanzonline.bmf.gv.at/fonws/ws/sessionService.wsdl'

        print("""  
                -------------------------Finanzonline-------------------------
        """)

        while True:
            try:
                sess_id = zeep.Client(wsdl=SESSION_URL).service.login(*list(SESSION_KEYS.values())).id
                print('Retrieval of Session-ID succefull')
                break
            except ValidationError:
                print('Retrieval of Session-ID failed, please contact system admin!')
                break
            except:
                print('Error accessing Finanzonline Service')
                return
                break

                
       
        LOGIN_KEYS['id'] = sess_id
        
        UID_URL = 'https://finanzonline.bmf.gv.at/fon/ws/uidAbfrage.wsdl'
        while True:
            try:
                server_response = zeep.Client(wsdl=UID_URL).service.uidAbfrage(*list(LOGIN_KEYS.values()))
                _ =zeep.Client(wsdl=SESSION_URL).service.logout(SESSION_KEYS['tid'], SESSION_KEYS['benid'],sess_id)
                response=zeep.helpers.serialize_object(server_response, dict)
                print('Access to Finanzonline successful')
                print(pd.Series(response))
                break
            except ValidationError:
                print('Authentication failed, please contact system admin!') 
                break
            except:
                print('Error accessing Finanzonline Service')
                break
      
        #MESSAGE = response['msg']
        
        
        
class ViesLookupStrategy(AbstractLookupStrategy):
    @staticmethod
    def get_info():
            print("""
                  Class to send a request to EU VAT VIES VAT Lookup Service
                  
                  Needed input: foreign VAT
                  
                  Return: validity, adress, company name
                  NOT WORKING
                  """)
    def SendRequest(self):
        print("""  
                -------------------------VIES-------------------------
        """)
        UID_URL = 'http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl'
        while True:
            try:
                server_response = zeep.Client(wsdl=UID_URL).service.checkVatApprox(countryCode = self.value['uid'][:2],
                                                                                     vatNumber = self.value['uid'][2:],
                                                                                     traderName = self.value['comp_name'],
                                                                                     traderCompanyType =self.value['comp_type'],
                                                                                     traderStreet = self.value['street'],
                                                                                     traderPostcode = self.value['zip'],
                                                                                     traderCity=self.value['city'])
                #server_response = zeep.Client(wsdl=UID_URL).service.checkVatResponse(self.value['uid'][:2],self.value['uid'][2:])
                response=zeep.helpers.serialize_object(server_response, dict)
                print('Access to VIES successful')
                print(pd.Series(response))
               
                break
            except ValidationError:
                print('Authentication failed, please contact system admin!')
                break
            except:
                print('Error accessing  VIES Service')
                break
      
        
        
        #MESSAGE = reponse['valid']
        
        


        
class BZStLookupStrategy(AbstractLookupStrategy):
    @staticmethod
    def get_info():
            print("""
                  Class to send a request to BZSt
                  
                  Needed input: own VAT and foreign VAT, company name, company type, adress
                  
                  Return: validity of VATID, adress, company name
                  """)
    
                 
                 

                 
    def SendRequest(self):
        print("""  
                -------------------------BZSt-------------------------
        """)
        ERROR_MSG = {'200': 'The requested VAT ID is valid.',
                 '201': 'The requested VAT ID is invalid.',
                 '202': 'The requested VAT ID is invalid. It is not registered in the requested state.',
                 '203': 'The requested VAT ID is invalid. It is valid from {} on.',
                 '204': 'The requested VAT ID is invalid. It was valid from {} until {}.',
                 '205': 'Ihre Anfrage kann derzeit durch den angefragten EU-Mitgliedstaat oder aus anderen Gründen nicht beantwortet werden.' 
                         +'Bitte versuchen Sie es später noch einmal. Bei wiederholten Problemen wenden Sie sich bitte an das Bundeszentralamt für Steuern - Dienstsitz Saarlouis.',
                 '206': 'Ihre deutsche USt-IdNr. ist ungültig. Eine Bestätigungsanfrage ist daher nicht möglich. Den Grund hierfür können Sie beim Bundeszentralamt für Steuern - Dienstsitz Saarlouis - erfragen.',
                 '207': 'Ihnen wurde die deutsche USt-IdNr. ausschliesslich zu Zwecken der Besteuerung des innergemeinschaftlichen Erwerbs erteilt. Sie sind somit nicht berechtigt, Bestätigungsanfragen zu stellen.',
                 '208': 'Für die von Ihnen angefragte USt-IdNr. läuft gerade eine Anfrage von einem anderen Nutzer. Eine Bearbeitung ist daher nicht möglich. Bitte versuchen Sie es später noch einmal.',
                 '209': 'Die angefragte USt-IdNr. ist ungültig. Sie entspricht nicht dem Aufbau der für diesen EU-Mitgliedstaat gilt.',
                 '210': 'Die angefragte USt-IdNr. ist ungültig. Sie entspricht nicht den Prüfziffernregeln die für diesen EU-Mitgliedstaat gelten.',
                 '211': 'Die angefragte USt-IdNr. ist ungültig. Sie enthält unzulässige Zeichen (wie z.B. Leerzeichen oder Punkt oder Bindestrich usw.).',
                 '212': 'Die angefragte USt-IdNr. ist ungültig. Sie enthält ein unzulässiges Länderkennzeichen.',
                 '213': 'Die Abfrage einer deutschen USt-IdNr. ist nicht möglich.',
                 '214': 'Ihre deutsche USt-IdNr. ist fehlerhaft. Sie beginnt mit DE gefolgt von 9 Ziffern.',
                 '215': 'Ihre Anfrage enthält nicht alle notwendigen Angaben für eine einfache Bestätigungsanfrage (Ihre deutsche USt-IdNr. und die ausl. USt-IdNr.). Ihre Anfrage kann deshalb nicht bearbeitet werden.',
                 '216': 'Ihre Anfrage enthält nicht alle notwendigen Angaben für eine qualifizierte Bestätigungsanfrage (Ihre deutsche USt-IdNr., die ausl. USt-IdNr., Firmenname einschl. Rechtsform und Ort).'
                         +'Es wurde eine einfache Bestätigungsanfrage durchgeführt mit folgenden Ergebnis: Die angefragte USt-IdNr. ist gültig.',
                 '217': 'Bei der Verarbeitung der Daten aus dem angefragten EU-Mitgliedstaat ist ein Fehler aufgetreten. Ihre Anfrage kann deshalb nicht bearbeitet werden.',
                 '218': 'Eine qualifizierte Bestätigung ist zur Zeit nicht möglich. Es wurde eine einfache Bestätigungsanfrage mit folgendem Ergebnis durchgeführt: Die angefragte USt-IdNr. ist gültig.',
                 '219': 'Bei der Durchführung der qualifizierten Bestätigungsanfrage ist ein Fehler aufgetreten. Es wurde eine einfache Bestätigungsanfrage mit folgendem Ergebnis durchgeführt: Die angefragte USt-IdNr. ist gültig.',
                 '220': 'Bei der Anforderung der amtlichen Bestätigungsmitteilung ist ein Fehler aufgetreten. Sie werden kein Schreiben erhalten.',
                 '221': 'Die Anfragedaten enthalten nicht alle notwendigen Parameter oder einen ungültigen Datentyp.',
                 '999': 'Eine Bearbeitung Ihrer Anfrage ist zurzeit nicht möglich. Bitte versuchen Sie es später noch einmal.'}
        
        REQUEST_DATA = {'UstId_1': self.value['uid'],'UstId_2':self.value['uid_tn'],
                        'Firmenname':self.value['comp_name'], 'Ort':self.value['city'], 'PLZ':self.value['zip'], 
                        'Strasse':self.value['street'], 'Druck' : 'ja'}
        
        UID_URL ='https://evatr.bff-online.de/evatrRPC?UstId_1={}&UstId_2={}&Firmenname={}&Ort={}&PLZ={}&Strasse={}&Druck={}'
        #with requests.Session() as s:
        while True:
            try:
                response = requests.get(url = UID_URL.format(*list(REQUEST_DATA.values())) )  
                response=re.findall(r'string>(\w*)</string', response.text)
        
                #requests über request.get enthalten keine Uhrzeit/datums info (?)
                response.remove('Uhrzeit')
                response.remove('Datum')
                response = dict(itertools.zip_longest(*[iter(response)] * 2, fillvalue=""))
                print('Access to BZSt successful')
                print(pd.Series(response))
                print(response['ErrorCode'])
                print(ERROR_MSG[response['ErrorCode']].format(response['Gueltig_ab'], response['Gueltig_bis']))
                break
            except:
                print('error')
                break
            
        #error messages
        #https://evatr.bff-online.de/eVatR/xmlrpc/codes
        
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input1', help='The VAT-ID for validation', type=str)
    parser.add_argument('input2', help='Own VAT_ID', default=None,nargs='?', type =str )
    

    
    #parser.add_argument('-out_file', help='Optional output file', default=0)
    args = parser.parse_args()

    parser = argparse.ArgumentParser()
    #print(args.input1)
    #print(args.input2)
    BZStLookupStrategy(args.input1, args.input2).SendRequest()
    FinanzonlineLookupStrategy(args.input1, args.input2).SendRequest()
    ViesLookupStrategy(args.input1, args.input2).SendRequest()
        
