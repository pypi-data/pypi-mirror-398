import requests
import xml.etree.ElementTree as ET
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
import re

'''
Next Steps:

1. Update the dict returns to accept return type of df -- completed
2. Create a function to validate the users headers -- completed
3. Create a to_df() method for the xml parser -- completed
4. Add a file retrieving class -- completed
5. See if it is possible to scrape BO tables??
6. Gather as of date for items -- completed
7. Update direct namespace calls to default xbrl namespaces from namespaces dict
8. Fix xml scraper - not returning data
'''

class FileGather:
    def __init__(self,email:str,return_type: str = "dict"):
        self.email = email
        self.headers = {"User-Agent":email}
        self.return_type = return_type
        if not self.__valid_email():
            raise ValueError("Invalid Email Address")

    def __valid_email(self):
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email))
    

    def recent_filings(self,file_type:list,limit:int=1000000):
        entry_date = []
        for file in file_type:
            length = 100
            start = 0
            while length == 100:
                # Create URL and send request
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type={file}&company=&dateb=&owner=include&start={start}&count=100&output=atom"
                data = requests.get(url=url,headers=self.headers)
                root = ET.fromstring(data.content)
                namespace = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", namespace)
                # Gather the filings from the xml doc
                for entry in entries:
                    entry_data = {
                        "title": entry.find("atom:title", namespace).text,
                        "link": entry.find("atom:link", namespace).get("href"),
                        "updated": entry.find("atom:updated", namespace).text,
                        "id": entry.find("atom:id", namespace).text,
                        "category": entry.find("atom:category", namespace).get("term") if entry.find("atom:category", namespace) is not None else None
                    }
                    entry_date.append(entry_data)
                length = len(entries)
                start += length 
                if start >= limit:
                    entry_date =  entry_date[:limit] 
                    break
        print(f"{len(entry_date)} entries found")
        if self.return_type == "df":
            entry_date = pd.DataFrame(entry_date)
        else:
            entry_date = entry_date
        return entry_date
    
    def __ticker_mapping(self):
        resp = requests.get("https://www.sec.gov/files/company_tickers.json",headers=self.headers).json()
        data = pd.DataFrame.from_dict(resp, orient='index')
        data["cik_str"] = data["cik_str"].astype("str").str.zfill(10)
        return data
    
    def __company_files_return(self,url,filing_type:list):
        try:
            result = requests.get(url,headers=self.headers)
            cik = result.json()["cik"]
            df = pd.DataFrame(result.json()["filings"]["recent"])
            df = df[df["form"].isin(filing_type)].reset_index(drop=True)
            df['cik'] = cik
            accession_num = df.loc[0,"accessionNumber"].replace("-","")
            doc = df.loc[0,"primaryDocument"]
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_num}/{doc}"
        except:
            print(f"Desired Filing Type Unavaliable for {url}")
        
        if self.return_type == 'dict':
            return df.to_dict()
        else:
            return df
    
    def __company_file_url(self,df):
            if self.return_type == 'dict':
                df = pd.DataFrame(df)
            accession_num = df.loc[0,"accessionNumber"].replace("-","")
            doc = df.loc[0,"primaryDocument"]
            cik = df.loc[0,"cik"]
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_num}/{doc}"
            return url





    def company_file(self, filing_type: list, id: str, id_type: str = "ticker"):
        mapping = self.__ticker_mapping()

        if id_type == "ticker":
            cik = mapping.loc[mapping["ticker"] == id, "cik_str"].iloc[0]
        else:
            cik = str(id).zfill(10)

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        return self.__company_file_url(
            self.__company_files_return(url=url, filing_type=filing_type)
        )

    

    def all_company_files(self, filing_type: list, id: str, id_type: str = "ticker"):
        mapping = self.__ticker_mapping()

        if id_type == "ticker":
            cik = mapping.loc[mapping["ticker"] == id, "cik_str"].iloc[0]
        else:
            cik = str(id).zfill(10)

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        return self.__company_files_return(url=url, filing_type=filing_type)

    
    
############################################################################################################
class SecCompany:
    def __init__(self,url:str,email:str,return_type:str = "dict"):
         # Set input data as vars
        self.url = url.replace("ix?doc=/","")
        self.url = self.url.split("/")[:-1]
        self.url = '/'.join(self.url)
        self.email = email
        self.headers = {"User-Agent":email}
        self.return_type = return_type
        # Validate URL upon and Headers 
        if not self.__valid_url():
            print(f"Invalid SEC URL format: {self.url}")
        if not self.__valid_email():
            raise ValueError("Invalid Email Address")
        
        self.html_url = self.__get_html_file()
        


    def __valid_url(self):
        return "https://www.sec.gov/Archives/edgar/data/" in self.url
    
    def __valid_email(self):
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email))
    
    def get_files(self):
        # Gather HTML and scrape table
        resp = requests.get(url=self.url,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')
        # Convert table to dict
        html_table = soup.find('table')
        headers = [header.text for header in soup.find_all("th")]
        table_data = [[cell.text for cell in row("td")]
                         for row in BeautifulSoup(str(html_table),features="lxml")("tr")]
        table_dict = [dict(zip(headers, row)) for row in table_data]
        result = {"Base File":self.url,"Sub File":table_dict}
        return result
    
    def __get_html_file(self):
        files = self.get_files()
        file_url = files["Base File"] +'/' + [item["Name"] for item in files["Sub File"] if "Name" in item and item["Name"].endswith("-index-headers.html")][0]
        resp = requests.get(url=file_url,headers=self.headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        # get the first <a> tag
        first_a = soup.find("a")
        file_nm = first_a.get("href")
        html_url = self.url + '/' + file_nm
        return html_url
    
    def __get_xml_file(self):
        files = self.get_files()
        file_url = files["Base File"] + "/" + [item["Name"] for item in files["Sub File"] if "Name" in item and "_htm.xml" in item["Name"]][0]
        file_date = [item["Last Modified"] for item in files["Sub File"] if "Name" in item and "_htm.xml" in item["Name"]][0]
        resp = requests.get(url=file_url,headers=self.headers).content
        return [resp,file_date]
    
    def __get_namespaces(self):

        xml = self.__get_xml_file()
        xml_content = xml[0]
        file_date = xml[1]
        # Convert bytes to a file-like object 
        xml_file = BytesIO(xml_content)
        # Parse the XML content
        it = ET.iterparse(xml_file, events=['start-ns'])
        namespaces = dict([node for _, node in it])
        if '' in namespaces:
            namespaces['xbrl'] = namespaces['']
            del namespaces['']
        return [xml_content,namespaces,file_date]

    def __attr_scraper(self, attributes: list, root, namespaces,file_date):
        # Standard company data
        company_info = {
            'name': root.findall('.//dei:EntityRegistrantName', namespaces),
            'cik': root.findall('.//dei:EntityCentralIndexKey', namespaces),
            'tickers': root.findall('.//dei:TradingSymbol', namespaces)
        }

        # Safely build Ticker-to-Class mapping
        share_class_dict = {'us-gaap:CommonStockMember':company_info['tickers'][0].text.strip()} if len(company_info['tickers']) == 1 else {"N/A":None}
        for elem in company_info["tickers"]:
            context_ref = elem.attrib.get("contextRef")
            if not context_ref:
                continue
            context = root.find(f'.//{{http://www.xbrl.org/2003/instance}}context[@id="{context_ref}"]')
            if context is None:
                continue
            explicit = context.find('.//xbrldi:explicitMember[@dimension="us-gaap:StatementClassOfStockAxis"]',
                                    namespaces=namespaces)
            if explicit is not None and explicit.text:
                share_class_dict[explicit.text.strip()] = elem.text.strip() if elem.text else None

        # Flatten values in company_info
        for key in company_info:
            company_info[key] = [elem.text for elem in company_info[key] if elem.text]

        company_info["name"] = company_info["name"][0] if company_info["name"] else None
        company_info["cik"] = company_info["cik"][0] if company_info["cik"] else None
        company_info["url"] = self.url
        company_info["file_date"] = file_date



        # Extract and tag requested attributes
        attribute_roots = {tag: root.findall(f'.//{tag}', namespaces) for tag in attributes}
        for tag in attribute_roots:
            data_list = []
            for elem in attribute_roots[tag]:
                try:
                    context_id = elem.attrib.get("contextRef")
                    id = elem.attrib.get("id")
                    context = root.find(f'.//{{http://www.xbrl.org/2003/instance}}context[@id="{context_id}"]') if context_id else None
                    explicit_member = context.find('.//xbrldi:explicitMember[@dimension="us-gaap:StatementClassOfStockAxis"]',
                                                namespaces=namespaces) if context is not None else None
                    # Extract period dates
                    instant_elem = context.find('.//{http://www.xbrl.org/2003/instance}period/{http://www.xbrl.org/2003/instance}instant') if context is not None else None
                    start_elem   = context.find('.//{http://www.xbrl.org/2003/instance}period/{http://www.xbrl.org/2003/instance}startDate') if context is not None else None
                    end_elem     = context.find('.//{http://www.xbrl.org/2003/instance}period/{http://www.xbrl.org/2003/instance}endDate') if context is not None else None


                    if explicit_member is not None and explicit_member.text:
                        class_tag = explicit_member.text.strip()
                    elif len(attribute_roots[tag]) == 1:
                        class_tag = "us-gaap:CommonStockMember"
                    else:
                        class_tag = "multi-value"

                    date_val  = instant_elem.text if instant_elem is not None and instant_elem.text else None
                    start_val = start_elem.text if start_elem is not None and start_elem.text else None
                    end_val   = end_elem.text if end_elem is not None and end_elem.text else None
                    ticker_val = share_class_dict.get(class_tag, None)
                    value = elem.text if elem.text else None
                    location_url = self.html_url + '#' + id

                    data_list.append([ticker_val, value, date_val, start_val, end_val, class_tag,location_url])
                except Exception as e:
                    data_list.append([None, elem.text if elem.text else None, None, None, None, None,None])
            attribute_roots[tag] = data_list

        # Build return dict or DataFrame
        result = {
            "Company Info": company_info,
            "data": attribute_roots
        }

        if self.return_type == "df":
            rows = []
            for tag, records in result["data"].items():
                if not records:
                    rows.append([
                        company_info["url"],
                        pd.to_datetime(company_info["file_date"], errors='coerce'),
                        company_info["name"],
                        company_info["cik"],
                        company_info["tickers"],
                        tag,
                        pd.NA,pd.NA,pd.NA,pd.NA,pd.NA,pd.NA,pd.NA
                    ])
                else:
                    for row in records:
                        rows.append([
                            company_info["url"],
                            pd.to_datetime(company_info["file_date"], errors='coerce'),
                            company_info["name"],
                            company_info["cik"],
                            company_info["tickers"],
                            tag,
                            row[0], 
                            row[1], 
                            pd.to_datetime(row[2],errors='coerce'), 
                            pd.to_datetime(row[3],errors='coerce'), 
                            pd.to_datetime(row[4],errors='coerce'), 
                            row[5],
                            row[6]
                        ])
            result = pd.DataFrame(rows, columns=[
                "url", "file_date","name", "cik", "public_tickers", "data_tag",
                "val_associated_ticker", "val", "date", "period_start","period_end","class_type","location_url"
            ])


        return result

    def xml_parser(self,attributes:list):
        try:
            xml_file,ns,file_date = self.__get_namespaces()
            root = ET.fromstring(xml_file)
            results = self.__attr_scraper(attributes,root,ns,file_date)
            return results
        except Exception as e:
            print(f"Error with {self.url}")


############################################################################################################

def get_tickers(email):
    def __valid_email(email):
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    
    if not __valid_email(email):
        raise ValueError("Invalid Email Address")

    result = requests.get("https://www.sec.gov/files/company_tickers.json",headers={"User-Agent":email})

    df = pd.DataFrame.from_dict(result.json(),"index").reset_index(drop=True)
    df["cik_str"] = df["cik_str"].astype("str").str.zfill(10)
    return df


def get_close_price(ticker):
    try:
        headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Origin': 'https://www.nasdaq.com',
        'Referer': 'https://www.nasdaq.com/'
        }
        url = f"https://api.nasdaq.com/api/quote/{ticker}/summary?assetclass=stocks"
        req = requests.get(url, headers=headers)
        price = float(req.json()["data"]["summaryData"]["PreviousClose"]["value"].replace("$","").replace(",",""))
    except:
        price = None
    return [ticker,price]