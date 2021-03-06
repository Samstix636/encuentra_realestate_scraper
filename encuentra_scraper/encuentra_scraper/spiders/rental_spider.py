import scrapy
from scrapy import Request
import datetime

today = datetime.datetime.now().strftime("%d/%m/%Y")

def days_between(d1, d2):
    d1 = datetime.datetime.strptime(d1, "%d/%m/%Y")
    d2 = datetime.datetime.strptime(d2, "%d/%m/%Y")
    return abs((d2 - d1).days)

class RentalSpiderSpider(scrapy.Spider):
    location=['Costa Del Este','Punta Pacifica', 'Avenida Balboa','Santa Maria','Coco Del Mar', 'Casco Viejo']
    # location=['Costa Del Este']

    urls=['https://www.encuentra24.com/panama-es/bienes-raices-alquiler-apartamentos/prov-panama-ciudad-de-panama-costa-del-este?q=number.50',
           'https://www.encuentra24.com/panama-es/bienes-raices-alquiler-apartamentos?q=number.50|keyword.punta+pacifica',
           'https://www.encuentra24.com/panama-es/bienes-raices-alquiler-apartamentos?q=number.50|keyword.avenida+balboa',
           'https://www.encuentra24.com/panama-es/bienes-raices-alquiler-apartamentos?q=number.50|keyword.santa+maria',
           'https://www.encuentra24.com/panama-es/bienes-raices-alquiler-apartamentos?q=number.50|keyword.coco+del+mar',
           'https://www.encuentra24.com/panama-es/bienes-raices-alquiler-apartamentos?q=number.50|keyword.casco+viejo'
           ]

    name = 'rental_spider'
    # allowed_domains = ['www.google.com']
    # start_urls = ['http://www.google.com/']
    # max_retries=2

    def start_requests(self):
        for i in range(6):    
            yield Request(
                    url = self.urls[i],
                    callback=self.parse_search_apartments,
                    dont_filter=True,
                    meta={'counter':1, 'location':self.location[i]}
                )

    def parse_search_apartments(self, response):
        location=response.meta["location"]
        counter=response.meta['counter']
        # if counter<3:
        counter+=1
        partial_urls=response.xpath("//div[@class='ann-box-details']/a/@href").extract()
        for url in partial_urls:
            apartment_url='https://www.encuentra24.com'+url
            yield Request(url=apartment_url, callback=self.parse_apartment_details, meta = {'dont_redirect':True,'location':location,'link':apartment_url, "handle_httpstatus_list" : [301, 302, 303]},dont_filter=True)
        next_rel_url=response.xpath("//a[@title='Continuar']/@href").extract_first()
        if next_rel_url:
            absolute_url='https://www.encuentra24.com'+next_rel_url
            yield Request(url=absolute_url,callback=self.parse_search_apartments,dont_filter=True, meta={'counter':counter, 'location':location,"handle_httpstatus_list" : [301, 302, 303]})

    def parse_apartment_details(self, response):
        location=response.meta["location"]
        link=response.meta["link"]
        name=response.xpath("//h1[@class='product-title']/text()").extract_first()
        try:
            name=name.split('|')[1]
        except:
            pass
        date=response.xpath("//span[text()='Enviado:']/following-sibling::span/text()").extract_first()
        Price=response.xpath("//span[text()='Alquiler:']/following-sibling::span/text()").extract_first()
        msq=response.xpath("//span[text()='M?? de construcci??n:']/following-sibling::span/text()").extract_first()
        price_per_msq=response.xpath("//span[text()='Alquiler//M?? de construcci??n:']/following-sibling::span/text()").extract_first()
        bedroom=response.xpath("//span[text()='Recamaras:']/following-sibling::span/text()").extract_first()
        if msq is None:
            msq=response.xpath("//span[text()='Tama??o del Lote:']/following-sibling::span/text()").extract_first()
            price_per_msq=response.xpath("//span[text()='Alquiler/M?? de terreno:']/following-sibling::span/text()").extract_first()
        if name:
            no_of_days=days_between(date, today)
            if no_of_days<30:
                post_status='Recent Post(less than 30days)'
            elif no_of_days>30 and no_of_days<90:
                post_status='Mid Post(30-90 days)'
            else:
                post_status='Old Post(Over 90days)'

            yield{
                'Apartment Name':name,
                'City':location,
                'Days since Post':post_status,
                'Price':Price,
                'M?? of Construction(Size)':msq,
                'Rent/M??':price_per_msq,
                'No of Bedrooms':bedroom,
                'Property Url':link

                }

