from msilib.schema import Error
import sys
import os
import re
import pytz
import datetime
import scrapy
import json
import pymysql
import requests
import random
import time
import mysql.connector
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from datetime import datetime
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.http import HtmlResponse
from w3lib.html import remove_tags
from scrapy.spiders.init import InitSpider
from slugify import slugify
from itertools import repeat
import utils
from db_helper import DBAction
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from scrapy.utils.log import configure_logging



class ZEPTOPDPSPIDER(InitSpider):
    name = "zepto_pdp"
    allowed_domains = ["shop.zeptonow.com"]
    start_urls = ["https://shop.zeptonow.com/Home"]
    custom_settings = {
            # specifies exported fields and order
            "DOWNLOAD_TIMEOUT": 60000,
            "DOWNLOAD_MAXSIZE": 12406585060,
            "DOWNLOAD_WARNSIZE": 0,
            "CONCURRENT_REQUESTS": 1,
            "CONCURRENT_REQUESTS_PER_DOMAIN":1,
            "CONCURRENT_REQUESTS_PER_IP":1,
            "HTTPPROXY_ENABLED": True,
            "DOWNLOADER_MIDDLEWARES" : {
                "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
                "scrapy_web_crawlers.middlewares.RandomUserAgentMiddleware": 1
                },
            "LOG_ENABLED":True
        }    
    HOME_URL = "https://shop.zeptonow.com/Home/"
    
    def __init__(self, inputs, **kw): # inputs,
        super(ZEPTOPDPSPIDER, self).__init__(**kw)
        self.inputs = inputs
        self.tz = inputs.get("tz")
        self.current_time = inputs.get("current_time")
        self.dt = inputs.get("dt")
        self.timestamp = inputs.get("timestamp")

        print("PF ID: "+inputs.get("pf_id"))
        print("SKU ID: "+inputs.get("sku_id"))
        print("WEB PID: "+inputs.get("web_pid"))
        print("URL: "+inputs.get("page_url"))
        print("LOCATION: "+inputs.get("location"))
        print("LOCATION ID: "+inputs.get("location_id"))
        print("PINCODE: "+inputs.get("pincode"))
        print("crawl_id: "+inputs.get("crawl_id"))
        
        self.site = self.name
        self.env = inputs.get("env")
        self.db_name = inputs.get("db_name")        
        self.crawl_id = int(inputs.get("crawl_id"))
        self.pf_id = int(inputs.get("pf_id"))
        self.sku_id = int(inputs.get("sku_id"))      
        self.web_pid = inputs.get("web_pid")
        self.pdp_page_url = inputs.get("page_url")
        self.brand_id = int(inputs.get("brand_id"))
        self.brand_name = inputs.get("brand_name")

        self.location_search = inputs.get("location_search")
        self.location_id = int(inputs.get("location_id"))
        self.location = inputs.get("location")
        self.pincode = inputs.get("pincode")

        self.base_dir = os.path.join(os.getcwd(), "logs", self.site)
        self.output_file = os.path.join(self.base_dir, "output", f"{self.pincode}_{self.web_pid}.txt")
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        self.output_cols = [
            "pf_id",
            "crawl_id",
            "sku_id",
            "web_pid",
            "pdp_title_value",
            "brand_id",
            "brand_name",
            "price_rp",
            "price_sp",
            "pdp_rating_value",
            "pdp_review_count",
            "pdp_rating_count",
            "pdp_qa_count",
            "pdp_desc_value",
            "pdp_image_count",
            "pdp_image_url",
            "pdp_image_url_all",
            "osa",
            "osa_remark",
            "pdp_page_url",
            "pdp_discount_value",
            "location_id",
            "location_name",
            "pincode",
            "created_by",
            "created_on",
            "status"
        ]
        
        self.visit_count = str(random.choice([10,11,12,13]))        
        
        self.db_action = DBAction()
        try:
            self.connection = self.db_action.db_connection(db_name=self.db_name, env=self.env)
            self.cursor = self.connection.cursor()
        except mysql.connector.Error as error:
            self.logger.error("MySQL Error: "+error)
            print("Connection error with the database", error)
        self.session = requests.Session()
        self.logger.info("Home Page Request")

    def init_request(self):    
        #Home Page Request
        self.logger.info("Home Page Request")

        response = self.web_pid_search(self.session)
        #print(response)
        records = self.parse_detail_page(response)
        #print(records)
        self.logger.info("Data inserting")

        tbl_columns_str = "`"+"`,`".join(self.output_cols)+"`"        
        values_list = []
        values_list.extend(repeat("%s", len(self.output_cols)))
        tbl_columns_val = ",".join(values_list)
        mySql_insert_query = """INSERT INTO `zepto_crawl_pdp` (""" +tbl_columns_str+ """) VALUES (""" +tbl_columns_val+ """)"""
        print(mySql_insert_query)
        rec = []
        if len(records):
            for i in self.output_cols:
                if i in records:
                    rec.append(str(records[i]))
                else:
                    rec.append("")
            print("Data Inserting")
        else:
            print("No Records Found",self.web_pid)
        #print(rec)
        try:
            self.cursor.executemany(str(mySql_insert_query), [tuple(rec)])
            self.connection.commit()
        except self.cursor.Error as err:
            self.logger.error("Mysql Error occured: {}".format(str(err))) 
        except:
            self.logger.error("Error Occured in records")
            self.logger.info(rec)

    def web_pid_search(self, session):
        store_dict={
            '110005' :'11e51a0e-6d44-4a9e-96db-7dbf50aae74b',
            '122008' : '91cdc5c9-2a07-4259-a78c-c93c9f2a44b3',
            '122022' : 'a7fa4b91-855a-4eb8-a89c-a36f1b20c617',
            '201001' :'2027ae67-e366-4f60-ab7d-64ffbebfeee0' ,
            '401107' :'73bfbb51-d67b-4eff-9a4f-37c044022f89',
            '201301' :'6f792c68-6524-4b40-b401-4e247e4ccbbb' ,
            '201305' :'73bfbb51-d67b-4eff-9a4f-37c044022f89' ,
            '400063' :'a5d48a70-31d9-4c5f-b61f-daae4ab4e3b3' ,
            '400015' :'c24dc1bf-c103-48cb-94e7-ef38c3b61687',
            '400601' :'2c911eaa-a276-47bc-92d8-447d166f2dfa',
            '411045' :'60252717-a8c5-4891-9b23-3db778b14477',
            '411014' :'0058ed07-4fa8-44ef-9cf1-bb8c038fb0b8',
            '560038' :'7de4838b-ae7c-44d0-bf24-fb2040666654',
            '600029' :'4dfe4a2c-117f-41a6-8cec-ebb1b4d2d846',
            '700038' :'9720e3fc-52dc-4305-b625-d69e45642fb0',
            '700064' :'1bc8fe29-c491-4fb3-94d4-81a6151d4f6b',
            '110018' :'aa443b4b-bf3b-499c-a846-bf5196d444ae' , 
            '122103' :'9a51d2b1-9708-4648-a294-0f5a5909cf5a' ,
            '201006' :'14003a93-4181-4118-a3ad-53fc46b6db7e' ,
            '201014' :'25a6f08a-839c-44fd-850b-902a69e3d54a' ,
            '201009' :'4f8f3e7f-09f6-4bea-924e-c29764c91e48' ,
            '400101' :'ac8009fb-db76-4e5a-af52-d513ba3f31ca' ,
            '560068' :'cf4a3845-f777-4857-bb14-54e061e452f6' ,
            '700091' :'1bc8fe29-c491-4fb3-94d4-81a6151d4f6b',
            '560026':'fa5e892d-65d7-4da6-9bde-e1f22deb7b6f',
            '560086' : '88814645-7b2b-4845-886b-d6c2e7471ef4',
            '560002' : '917d20a7-58e4-4574-95dd-dfe3513dd1b2',
            '560070' :'52d8a0f5-1c05-4afc-8259-c3d2d056b565',
            '560073' : '0a357d97-30cb-4eb4-a4b8-0e1fba2471d8',
            '560053' : 'e23e3990-bd88-43ed-a5d1-adf05c4ab60e',
            '560085' : '52d8a0f5-1c05-4afc-8259-c3d2d056b565',
            '560043' : '0a357d97-30cb-4eb4-a4b8-0e1fba2471d8',
            '560017' : '17141f08-6ccd-4d8b-ae18-0bd9ebbb8a40',
            '560001' : '7de4838b-ae7c-44d0-bf24-fb2040666654',
            '603103' : 'bc653ab4-3f2c-48d9-bd75-451553e01323',
            '560009' : 'b1403534-cd6b-49d0-a7cd-ce20e6497768',
            '560025' : 'ff1fc8e6-9f22-4c75-b7cf-15a5bd19be91',
            '560076' : 'ff1fc8e6-9f22-4c75-b7cf-15a5bd19be91',
            '560004' : '7c3e8dc3-8781-489c-a2c7-8f8f67149083',
            '560046' : '17141f08-6ccd-4d8b-ae18-0bd9ebbb8a40',
            '560010' : '2c0819dc-dd1f-4f37-b8e3-bae48c3eead9',
            '560049' : '0a5e41a0-7252-43f6-9e8f-9a1e5d48ddd3',
            '560056' : '7e880b31-ab99-476c-ae7e-a825d9af6890',
            '560068' : 'cf4a3845-f777-4857-bb14-54e061e452f6',
            '560093' : '7065f011-6c65-4186-99ee-7c1cdd56d581',
            '560018' : '52d8a0f5-1c05-4afc-8259-c3d2d056b565',
            '560040' : '7c3e8dc3-8781-489c-a2c7-8f8f67149083',
            '560097' : '6845a550-4826-4d3c-bfe8-eeb7d793a148',
            '560061' : 'ae43241e-255b-4c36-8275-c775b91b4028',
            '560036' : '0a5e41a0-7252-43f6-9e8f-9a1e5d48ddd3',
            '560029' : '5557ae84-a272-4f60-9b3e-12991b8237d6',
            '560062' : '23e6d099-8f3c-4cce-b269-82783be7427e',
            '560037' : '57e4f1a0-c553-49fa-9163-e4ad43177daf',
            '560071' : '7de4838b-ae7c-44d0-bf24-fb2040666654',
            '560016' : '67bd4b56-9ff9-432a-a918-9192a4dd1954',
            '560100' : '2fc49058-22eb-42c9-9860-9d0ca50712ec',
            '560005' : '17141f08-6ccd-4d8b-ae18-0bd9ebbb8a40',
            '500017' :'1712e422-5717-4540-88ff-b22ef46f4963',
            '500035':'6db6db5b-66be-40bb-992f-763dcc96bcfe',
            '500036':'fa5e892d-65d7-4da6-9bde-e1f22deb7b6f',
            '500038':'6db6db5b-66be-40bb-992f-763dcc96bcfe',
            '500061':'63df153e-ec91-4081-9edd-244c640d4649',
            '500063':'ca1a84e7-ef3d-4c27-8fe1-019df69cd7bb',
            '500067':'2dd497f8-2aae-496d-a104-9b996b743016',
            '500071':'ebda3286-c632-4006-9315-f16801470a0a',
            '500074':'6db6db5b-66be-40bb-992f-763dcc96bcfe',
            '500076':'1712e422-5717-4540-88ff-b22ef46f4963',
            '500085':'0d2079ea-909a-45c8-b1b8-313c26dfe5af',
            '500084':'2d8ae8c3-c7c3-4826-8802-e386af7f5385',
            '110017':'74c0b70e-3ba7-474c-8217-d2551cde2f57',
            '500095':'ca1a84e7-ef3d-4c27-8fe1-019df69cd7bb',
            '560003':'2c0819dc-dd1f-4f37-b8e3-bae48c3eead9',
            '560024':'6047c8fe-15ed-4c61-8d3e-060e800702f5',
            '560030':'72171562-3177-44fc-a11e-e62d8e656cfd',
            '560034':'72171562-3177-44fc-a11e-e62d8e656cfd',
            '560045':'c48dd700-4314-4cc1-bffa-e1344e0298dc',
            '560047':'b1403534-cd6b-49d0-a7cd-ce20e6497768',
            '560050':'0a357d97-30cb-4eb4-a4b8-0e1fba2471d8',
            '560064':'6845a550-4826-4d3c-bfe8-eeb7d793a148',
            '560092':'9062b527-4172-4da5-b40e-f349939e435e',
            '500045' : '88814645-7b2b-4845-886b-d6c2e7471ef4',
            '500012' : 'ecd31c34-5fdd-4be1-943e-9ea741670f15',
            '500015' : 'ec219202-e2cb-4726-b5e6-d0e6fc6025db',
            '500044' : '63df153e-ec91-4081-9edd-244c640d4649',
            '500013' : 'a898c8dc-70a7-4af3-9bf8-7907d6d6f5de',
            '500040' : '6c7369eb-b309-4cab-b165-6ed9d54b5b96',
            '500020' : '63df153e-ec91-4081-9edd-244c640d4649',
            '500034' : 'b2b682f4-7010-4945-b0bf-6e55df78f39d',
            '500027' : 'ca1a84e7-ef3d-4c27-8fe1-019df69cd7bb',
            '560065' : '6845a550-4826-4d3c-bfe8-eeb7d793a148',
            '560019' : '2c0819dc-dd1f-4f37-b8e3-bae48c3eead9',
            '560021' : '52d8a0f5-1c05-4afc-8259-c3d2d056b565',
            '560022' : '917d20a7-58e4-4574-95dd-dfe3513dd1b2',
            '560013' : '9e88e823-8755-42c9-a8f4-6b17499952a3',
            '560087' : '43dc610a-b80c-43e1-ac35-2d899d88795d',
            '560008' : '7de4838b-ae7c-44d0-bf24-fb2040666654',
            '560051' : 'f4259b1e-db6c-4266-9524-dbf0a2d54dfa',
            '560102' : '00db393a-dc6a-477d-9c36-f909a1632844',
            '560104' : '7c3e8dc3-8781-489c-a2c7-8f8f67149083',
            '560048' : '3a44ca1a-adde-4f8e-9e0c-613a98d348b7',
            '560094' : '6047c8fe-15ed-4c61-8d3e-060e800702f5',
            '560066' : 'fa5e892d-65d7-4da6-9bde-e1f22deb7b6f',
            '560038' : '7de4838b-ae7c-44d0-bf24-fb2040666654',
            '560078' : '23e6d099-8f3c-4cce-b269-82783be7427e',
            '560006' : 'f4259b1e-db6c-4266-9524-dbf0a2d54dfa',
            '560041' : 'cf384ecd-5e1f-47e9-9194-8e9dc940e8c3',
            '560069' : 'cf384ecd-5e1f-47e9-9194-8e9dc940e8c3',
            '560011' : 'cf384ecd-5e1f-47e9-9194-8e9dc940e8c3',
            '560020' : '2c0819dc-dd1f-4f37-b8e3-bae48c3eead9',
            '560084' : '17141f08-6ccd-4d8b-ae18-0bd9ebbb8a40',
            '560096' : '917d20a7-58e4-4574-95dd-dfe3513dd1b2',
            '560098' : '1541236b-63c6-42ce-b34e-9a57b7221ab5',
            '560054' : '9e88e823-8755-42c9-a8f4-6b17499952a3',
            '560023' : '2c0819dc-dd1f-4f37-b8e3-bae48c3eead9',
            '560033' : '17141f08-6ccd-4d8b-ae18-0bd9ebbb8a40',
            '560055' : '2c0819dc-dd1f-4f37-b8e3-bae48c3eead9',
            '560072' : '924b6b05-bdd2-4802-bc71-291bc1655129',
            '560039' : '7c3e8dc3-8781-489c-a2c7-8f8f67149083',
            '560075' : '7de4838b-ae7c-44d0-bf24-fb2040666654',
            '560032' : 'c48dd700-4314-4cc1-bffa-e1344e0298dc',
            '560058' : 'e23e3990-bd88-43ed-a5d1-adf05c4ab60e',
            '560059' : '7e880b31-ab99-476c-ae7e-a825d9af6890',
            '560080' : 'f4259b1e-db6c-4266-9524-dbf0a2d54dfa',
            '560027' : 'b1403534-cd6b-49d0-a7cd-ce20e6497768',
            '560042' : 'f4259b1e-db6c-4266-9524-dbf0a2d54dfa',
            '560028' : 'cf384ecd-5e1f-47e9-9194-8e9dc940e8c3',
            '560052' : '0cfef302-6106-4f54-a8fa-c614ab221f5f',
            '560091' : '924b6b05-bdd2-4802-bc71-291bc1655129',
            '500020':'63df153e-ec91-4081-9edd-244c640d4649',
            '500034':'5f858ea5-55fe-4b9d-8e65-847b7b5f8c09',
            '500027':'ca1a84e7-ef3d-4c27-8fe1-019df69cd7bb',
            '500016':'ada60f46-a0a6-4737-9ed4-614f58c1b6ed',
            '500003':'ada60f46-a0a6-4737-9ed4-614f58c1b6ed',
            '500018':'13ffc117-24d6-4854-a53e-a51d7330973e',
            '500080':'63df153e-ec91-4081-9edd-244c640d4649',
            '500039':'dbd6a04a-5071-4177-aaa9-b7ce6950fd2b',
            '500024':'ca1a84e7-ef3d-4c27-8fe1-019df69cd7bb',
            '500081':'382bda46-65fe-4e1e-b0c2-427128b594fa',
            '500008':'bb713aac-cd12-4b4d-9026-704e3deaaac3',
            '500028':'bb713aac-cd12-4b4d-9026-704e3deaaac3',
            '500060':'6db6db5b-66be-40bb-992f-763dcc96bcfe',
            '500029':'ca1a84e7-ef3d-4c27-8fe1-019df69cd7bb',
            '500025':'63df153e-ec91-4081-9edd-244c640d4649',
            }


                                                             
        #     "gurgaon": "0150afeb-5eb0-4219-a3ed-9a8f7018ffd3",
        #     "bangalore":"0f5f31f2-f764-498a-9cc5-606cf82f4f2e",
        #     "hyderabad":"382bda46-65fe-4e1e-b0c2-427128b594fa",
        #     "chennai":"6bb0999c-096f-4f5f-a23a-7d862f82400b",
        #     "pune":"60252717-a8c5-4891-9b23-3db778b14477",
        #     "mumbai":"751c003c-bbe4-453d-ae3d-404380528149",
        #     "new delhi":"6fb21f69-a868-4e72-b904-647f18038981"
        # }
        store_id = store_dict[self.pincode.strip()]
        session = requests.Session()
        payload = {
            "product_id": self.web_pid ,
            "store_id":store_id
        }
        headers={
                "accept":"application/json",
                "accept-encoding":"gzip, deflate, br",
                "accept-language":"en-US,en;q=0.9",
                "access-control-allow-credentials":"true",
                "access-control-allow-methods":"GET, POST, OPTIONS",
                "access-control-allow-origin":"*",
                "appversion":"0.0.1",
                "authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTI0MjkwMDQsInN1YiI6ImMzODliYjY0LTE0YTYtNDM5NS05ZmRhLTI5ZDZlZmRkOWUxMiJ9.bRucmJienNJvvp1E7nkRe1qsktEX-1tjzO-YvbLflOM",
                "bundleversion":"1",
                "compatible_components":"CONVENIENCE_FEE",
                "deviceuid":"536410cf4fab7aa04603511ff8d10cd1",
                "origin":"https://shop.zeptonow.com",
                "platform":"web",
                "referer":"https://shop.zeptonow.com/",
                "requestid":"1ac095bf-59ba-44d8-8cde-2e2b07cc32ab",
                "sec-ch-ua":'"Chromium";v="104", " Not A;Brand";v="99", "Microsoft Edge";v="104"',
                "sec-ch-ua-mobile":"?0",
                "sec-ch-ua-platform":"Windows",
                "sec-fetch-dest":"empty",
                "sec-fetch-mode":"cors",
                "sec-fetch-site":"cross-site",
                "sessionid":"29eec76a-e500-4af0-8d6d-06fddcca43de",
                "storeid":store_id,
                "systemversion":"Microsoft Edge 104.0.1293.54 null null Windows 10 64-bit Microsoft Edge 104.0.1293.54 on Windows 10 64-bit",
                "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36 Edg/104.0.1293.54",
                "x-requested-with":"XMLHttpRequest"
            }
        output = session.get(url = "https://api.zepto.co.in/api/v1/inventory/catalogue/product-detail/?product_id="+str(self.web_pid)+"&store_id="+str(store_id),data=payload,headers=headers)
        self.new_page_url = "https://api.zepto.co.in/api/v1/inventory/catalogue/product-detail/?product_id="+str(self.web_pid)+"&store_id="+str(store_id)
        self.logger.info("URL:-"+str(self.new_page_url))
        return output.text

    def parse_detail_page(self, data):
        output = json.loads(data)
        item = dict()
        flag = 0
        if 'product' in output:
            flag = 1
            web_pid = output['product']['id']
            pdp_title_value = output['product']['name']
            if len(output['product']['storeProducts'])>0:
                price_rp = str(int(output['product']['storeProducts'][0]['mrp'])/100)
                price_sp = str(int(output['product']['storeProducts'][0]['discountedSellingPrice'])/100)
                pdp_image_count = len(output['product']['storeProducts'][0]['productVariant']['images'])
                hero_image =""
                all_images = ""
                if int(pdp_image_count)>0:
                    hero_image = "https://ik.imagekit.io/jupdt2k6txi/tr:w-600,ar-1000-1000,pr-true/"+output['product']['storeProducts'][0]['productVariant']['images'][0]['path']
                    images_list = []
                    for ech in output['product']['storeProducts'][0]['productVariant']['images']:
                        images_list.append("https://ik.imagekit.io/jupdt2k6txi/tr:w-600,ar-1000-1000,pr-true/"+ech['path'])
                    all_images = ",".join(images_list)

                if not bool(output['product']['storeProducts'][0]['outOfStock']):
                    osa_remark = "IN STOCK"
                    osa = 1
                else:
                    osa_remark = "OSS"
                    osa = 0
                reseller_name_crawl = output['product']['manufacturerName']
                extracted_brand_name = output['product']['brand']
                discount = str(float(price_rp)-float(price_sp))
                if len(output['product']['description']):
                    description = output['product']['description'][0].strip()
                else:
                    description = ""
            else:
                osa_remark = "OSS"
                osa = 0

            item["marketplace"] = "Zepto"
            item["pf_id"] = self.pf_id
            item["crawl_id"] = self.crawl_id
            item["sku_id"] = self.sku_id
            item["pincode"] = self.pincode
            item["location_id"] = self.location_id
            item["location_name"] = self.location
            item["web_pid"] = self.web_pid
            item["brand_id"] = self.brand_id
            item["brand_name"] = self.brand_name
            item["extracted_web_pid"] = web_pid if web_pid else ""
            item["pdp_title_value"] = pdp_title_value if pdp_title_value else ""

            item["extracted_brand_name"] = extracted_brand_name if extracted_brand_name else ""

            item["pdp_rating_value"] = 0
            item["pdp_rating_count"] = 0
            item["pdp_review_count"] = 0
            item["pdp_qa_count"] =  0

            item["price_rp"] = price_rp if price_rp else 0.0
            item["price_sp"] = price_sp if price_sp else 0.0
            item["savings"] = str(float(price_rp)-float(price_sp))
            item["pdp_discount_value"] = discount if discount else 0.0
            item["pdp_desc_value"] = description

            item["pdp_image_count"] = pdp_image_count
            item["pdp_image_url"] = hero_image
            item["pdp_image_url_all"] = all_images
            item["aplus_images_list"] = ""
            item["ec_number_of_images"] = 0
            item["ec_number_of_videos"] = 0

            item["pdp_number_of_bulletin"] = 0
            item["pdp_bulletin_value"] = 0

            item["reseller_name_crawl"] = reseller_name_crawl
            item["seller_rank"] = 0
            item["best_sellers_rank"] = 0

            item["osa"] = osa
            item["osa_remark"] = osa_remark
            item['deal_flag'] = 0
            item["pdp_page_url"] = self.new_page_url
            item["created_by"] = "System"
            item["created_on"] = self.current_time
            item["status"] = 1

        else:
            print("Output Not Found for Web_pid",self.web_pid)
        
        if flag == 0:
            return []
        return item