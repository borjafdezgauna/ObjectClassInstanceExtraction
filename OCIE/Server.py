
from threading import Thread
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qsl
import CvNerProcessor

import os, time, datetime, re
from zipfile import ZipFile
import requests

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length'))
            body = self.rfile.read(content_len).decode('utf-8')
            #body = self.request.body.decode('utf-8')
            queryParameters = dict(parse_qsl(body, encoding='utf-8'))
            text = queryParameters['text']
            answer = self.server.NerProcessor.ProcessText(text)
            #url = urlparse(self.path)
            #queryParameters = parse_qsl(url)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(answer, "utf-8"))
            return
        except Exception as ex:
            pass

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Error. Failed to parse query parameters", "utf-8"))

    def do_GET(self):
        try:
            if "?" in self.path:
                _, squery = self.path.split("?", maxsplit=1)

                queryParameters = dict(parse_qsl(squery, encoding='utf-8'))
                text = queryParameters['text']
                answer = self.server.NerProcessor.ProcessText(text)
                #url = urlparse(self.path)
                #queryParameters = parse_qsl(url)
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(bytes(answer, "utf-8"))
                return
        except Exception as ex:
            pass

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Error. Missing parameters in request", "utf-8"))

class HttpServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class NerServer:
    def __init__(self, port):
        r = requests.post("https://xerkariak.com/xerkariak/apiV2/authenticate-v2.php", data= { 'UserId': 'borja.fernandez@ehu.eus', 'LicenseId' : "xerka-online", 'Password' : 'noPassword', 'Platform' : 'Windows 10 / Python' })

        pos = r.text.index('{')
        session = r.text[0:pos]
        print('Authenticated on server')

        #Download file
        self.DownloadFile('AcademicDegree.zip', session)
        self.DownloadFile('AcademicGrant.zip', session)
        self.DownloadFile('AcademicPhd.zip', session)
        self.DownloadFile('Annotations.zip', session)
        self.DownloadFile('Book.zip', session)
        self.DownloadFile('BookChapter.zip', session)
        self.DownloadFile('EducInnovProject.zip', session)
        self.DownloadFile('EducQualityEvaluation.zip', session)
        self.DownloadFile('EducTraining.zip', session)
        self.DownloadFile('IndexedJournalArticle.zip', session)
        self.DownloadFile('LanguageCertificate.zip', session)
        self.DownloadFile('Phd.zip', session)
        self.DownloadFile('ProceedingsArticle.zip', session)
        self.DownloadFile('ProfessionalJob.zip', session)
        #self.DownloadFile('ResearchPeriod.zip', session)
        self.DownloadFile('ResearchProject.zip', session)
        self.DownloadFile('Stay.zip', session)
        self.DownloadFile('StudentProject.zip', session)
        self.DownloadFile('Subject.zip', session)
        self.DownloadFile('PersonalData.zip', session)

        server = HttpServer(("localhost", port), Handler)
        server.NerProcessor = CvNerProcessor.Processor("models")
        self.server = server
        server.serve_forever()

    def Stop(self):
        self.server.shutdown()

    def DownloadFile(self, filename, session):
            try:
                tempDir = "temp/"
                tempFile = tempDir + filename
                outputDir = "models/"

                if not os.path.exists(tempDir):
                    os.makedirs(tempDir)
                if not os.path.exists(outputDir):
                    os.makedirs(outputDir)

                r = requests.post("https://xerkariak.com/xerkariak/apiV2/get-config-data-last-modified.php", data= { 'Id': '19', 'Session' : session, 'dataKey' : filename })
                match = re.search(r'Ok. (\d{4})-(\d{2})-(\d{2})', r.text)
                lastModifiedOnServer = None
                lastModifiedLocal = None
                if match != None:
                    lastModifiedOnServer = datetime.datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                if os.path.exists(tempFile):
                    lastModifiedLocal = datetime.datetime.fromtimestamp(os.path.getmtime(tempFile))
                if not(os.path.exists(tempFile)) or lastModifiedOnServer == None or (lastModifiedLocal != None and lastModifiedLocal < lastModifiedOnServer):
                    print('Downloading file: ' + filename)
                    r = requests.post("https://xerkariak.com/xerkariak/apiV2/get-config-data.php", data= { 'Id': '19', 'Session' : session, 'dataKey' : filename })
                    
                    with open(tempFile, 'wb') as f:
                        f.write(r.content)

                    with ZipFile(tempFile, 'r') as zip:
                        zip.extractall(outputDir)
                else:
                    print('Local file up-to-date: ' + filename)        
            except Exception as ex:
                print('Error: ' + ex)

server = NerServer(2222)