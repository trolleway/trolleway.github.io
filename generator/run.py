#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import urllib.request

from exif import Image
import shutil,logging

import pathlib
from datetime import datetime

class Website_generator():

    
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    def __init__(self):
        pass

    def numfill(self,value):
        return str(value).zfill(2)

    def dms_to_dd(self,d, m, s):
        dd = d + float(m)/60 + float(s)/3600
        return dd

    def  template_remove_map(self,template):
        txt = '''<!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- mapnik -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" integrity="sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A==" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js" integrity="sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA==" crossorigin=""></script>
    <!-- fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Prosto+One&display=swap" rel="stylesheet">
    <link href="../newsincerity.css" rel="stylesheet">
    <style>
    .bgimg-1 {bgimg}

    </style>
    </head>
    <body>

    <div class="bgimg-1">
    <div id="backwardlink"><a href="{url_left}" rel="{rel_left}" ><img src="../transparent.gif"></a></div>
    <div id="forwardlink"><a href="{url_right}" rel="{rel_right}" ><img src="../transparent.gif">{right_frist_image}</a></div>
      <div class="caption">
        <span class="border">
        {caption}
        </span><br>
      </div>
    </div>

    <footer>
    <div id="map" style="width: 100%; height: 400px;"></div>
    <div id="copyright">
           <a rel="cc:attributionURL" property="dc:title">Photo</a> by
           <a rel="dc:creator" href=""
           property="cc:attributionName">Artem Svetlov</a> is licensed to the public under
           the <a rel="license"
           href="https://creativecommons.org/licenses/by/4.0/">Creative
           Commons Attribution 4.0 License</a>.
    </div>
    <script>
    {map_js}
    </script>
    {google_counter}
    {yandex_counter}
    </footer>
    </body>
    </html>


        '''
        return txt


    def generate(self,mode=None):
    
        assert mode in ('standalone-full',None,'')
        
        basedir = (os.path.dirname(os.path.realpath(__file__)))
        json_dir = os.path.join(basedir,'content')
        
        if mode is None:
            sitemap_base_url = 'https://trolleway.github.io/texts/t/'
        if mode == 'standalone-full':
            sitemap_base_url = 'https://trolleway.com/reports/'
            
        sitemap_path_manual = os.path.join( 'sitemap_manual.xml') #, ".."+os.sep
        sitemap_path = os.path.join(os.getcwd(),'sitemap.xml')
        assert os.path.isfile(sitemap_path_manual),'not found file '+sitemap_path_manual
        #assert os.path.isfile(sitemap_path)
        pages2sitemap=[]

        #---- set output directory for files
        if mode is None:
            output_directory = os.path.join(os.getcwd(), ".."+os.sep,'texts','t')
        if mode == 'standalone-full':
            output_directory = os.path.join(basedir,'..','reports')
            if not os.path.isdir(output_directory): os.makedirs(output_directory)
            
        #---- copy static files
        src = os.path.join(basedir,'static')
        src_files = os.listdir(src)
        for file_name in src_files:
            full_file_name = os.path.join(src, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, output_directory)
            
            
        exif_cache_directory = os.path.join(os.getcwd(), 'exif_cache')
        if not os.path.isdir(exif_cache_directory):
            os.mkdir(exif_cache_directory)

        assert os.path.isdir(json_dir),'must exists directory "'+json_dir+'"'

        json_files = [f for f in os.listdir(json_dir) if os.path.isfile(os.path.join(json_dir, f)) and f.lower().endswith('.json')]
        assert len(json_files)>0,'must be find some .json files in '+json_dir

        #generate article for each json
        for json_filename in json_files:
            with open(os.path.join(json_dir,json_filename), encoding='utf-8') as json_file:
                try:
                    data = json.load(json_file)
                except Exception as e:

                    print('error open json '+os.path.join(json_dir,json_filename))
                    print(e)
                    print()
                    continue
            assert data is not None
            if 'date_mod' in data:
                GALLERY_DATE_MOD = data['date_mod']
            else:
                GALLERY_DATE_MOD = datetime.today().strftime('%Y-%m-%d')

            # target directory calc
            
            output_directory_name = os.path.splitext(json_filename)[0]
            output_directory_path = os.path.join(output_directory,output_directory_name)
            
            if not os.path.isdir(output_directory_path): 
                self.logger.debug('create '+output_directory_path)
                os.makedirs(output_directory_path)

            assert os.path.isdir(output_directory_path), 'must exist directory '+output_directory_path

            template_filepath = os.path.join(basedir, 'gallery.template.htm')
            assert os.path.exists(template_filepath), 'must exist file '+template_filepath
            with open(template_filepath, encoding='utf-8') as template_file:
                template = template_file.read()
            assert '{image_url}' in template

            template_index_filepath = os.path.join(basedir, 'gallery.index.template.htm')
            assert os.path.exists(template_index_filepath), 'must exist file '+template_index_filepath            

            count_images = len(data['images'])
            current_image = 0

            #calculate filenames for prev/next link
            
            for image in data['images']:
                current_image += 1

                if current_image < count_images:
                    url_right = self.numfill(current_image+1)+'.htm'
                    rel_right = 'next'
                else:
                    url_right = 'index.htm'
                    rel_right = 'up'
                if current_image > 1:
                    url_left = self.numfill(current_image-1)+'.htm'
                    rel_left = 'prev'
                else:
                    url_left = 'index.htm'
                    rel_left = 'up'

                if current_image == 1:
                    right_link_image = '''<img class="left_arrow"   alt="Go to next page" src="../Controls_chapter_next.svg">'''
                elif current_image == len(data['images']):
                    right_link_image = '''<img class="right_arrow"   alt="Go to index page" src="../Controls_eject.svg">'''
                else:
                    right_link_image = '''<img class="right_arrow"   alt="Go to next page" src="../Controls_chapter_next.svg">'''

                if current_image == 1:
                    left_link_image = '''<img class="left_arrow"  alt="Go to index page" src="../Controls_eject.svg">'''
                else:
                    left_link_image = '''<img class="right_arrow"   alt="Go to previous page" src="../Controls_chapter_previous.svg">'''


                # download photo from url to cache dir
                
                photo_filename = pathlib.Path(image['url']).name
                photo_local_cache = os.path.join(exif_cache_directory,photo_filename)
                if not os.path.exists(photo_local_cache):
                    try:
                        urllib.request.urlretrieve(image['url'], photo_local_cache)
                    except:
                        print('cant download '+image['url'])
                        
                #copy photo to website dir 
                
                if mode == 'standalone-full':
                    photo_static_website_path = os.path.join(output_directory_path,photo_filename)
                    if not os.path.isfile(photo_static_website_path):
                        self.logger.debug(photo_local_cache+' > '+photo_static_website_path)
                        try:
                            shutil.copyfile(photo_local_cache,photo_static_website_path)
                        except:
                            self.logger.debug('copy error '+ photo_local_cache)
                    image['url'] = photo_filename
                        
                # get photo coordinates from json if exists
                
                photo_coord = None
                photo_coord_osmorg = image.get('coord') or None

                if photo_coord_osmorg is not None:
                    photo_coord = photo_coord_osmorg.split('/')[0]+','+photo_coord_osmorg.split('/')[1]
                
                # get coordinates from exif
                
                if photo_coord is not None:
                    print('coordinates found in json '+photo_coord)
                else:
                    photo_coord='0,0'
                    #TODO: simplify, code taken from already exist script https://github.com/trolleway/photos2map/blob/master/photos2geojson.py
                    try:
                        with open(photo_local_cache, 'rb') as image_file:
                            image_exif = Image(image_file)
                            lat_dms=image_exif.gps_latitude
                            lat=self.dms_to_dd(lat_dms[0],lat_dms[1],lat_dms[2])
                            lon_dms=image_exif.gps_longitude
                            lon=self.dms_to_dd(lon_dms[0],lon_dms[1],lon_dms[2])

                            photo_coord=str(lat)+','+str(lon)
                            
                            lat = str(round(float(lat), 4))
                            lon = str(round(float(lon), 4))

                            self.logger.debug('coordinates obtained from EXIF data of image '+photo_coord)
                    except:
                        photo_coord='0,0'
                        lat='0'
                        lon='0'

                # print map
                
                map_center = data['map_center']
                if str(image.get('center_map'))=='1':
                    map_center = photo_coord
                map_js = '''
            var photo_coord = ['''+photo_coord+''']
            var map = L.map('map').setView(['''+map_center+'''], '''+data['map_zoom']+''');
            var OpenStreetMap_DE = L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            });
            var tiles = OpenStreetMap_DE.addTo(map);
            var circle = L.circle(photo_coord, {
                color: 'red',
                fillColor: '#f03',
                fillOpacity: 0.5,
                radius: 200
            }).addTo(map).bindPopup('Гиперссылка на картографический сервис');
                '''
                google_counter = """<!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-119801939-1"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', 'UA-119801939-1');
        </script>"""
                yandex_counter = '''<!-- Yandex.Metrika counter -->
        <script type="text/javascript" >
           (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
           m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
           (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

           ym(87742115, "init", {
                clickmap:true,
                trackLinks:true,
                accurateTrackBounce:true
           });
        </script>
        <noscript><div><img src="https://mc.yandex.ru/watch/87742115" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
        <!-- /Yandex.Metrika counter -->'''


                #build html
                
                html = str()
                #template = self.template_remove_map(template)
                with open(template_filepath, encoding='utf-8') as template_file:
                    template = template_file.read()
                html = template.format(
                image_url = image['url'],
                caption = image['text'],
                url_left = url_left,
                url_right = url_right,
                rel_left = rel_left,
                rel_right = rel_right,
                map_js = map_js,
                lat=lat,lon=lon,
                right_link_image = right_link_image,
                left_link_image = left_link_image,
                google_counter=google_counter,
                yandex_counter=yandex_counter
                )

                filename = os.path.join(output_directory_path,self.numfill(current_image))+'.htm'
                with open(filename, "w", encoding='utf-8') as text_file:
                    text_file.write(html)

                pages2sitemap.append({'loc':sitemap_base_url+output_directory_name+'/'+self.numfill(current_image)+'.htm','priority':'0.4','lastmod':GALLERY_DATE_MOD})
            pages2sitemap.append({'loc':sitemap_base_url+output_directory_name+'/'+'index.htm','priority':'0.6','lastmod':GALLERY_DATE_MOD})

            # index page
            with open(template_index_filepath, encoding='utf-8') as template_file:
                template = template_file.read()

            if 'text_en' in data:
                content_en = '<div class="en" >'+data['text_en']+'</div>'+"\n"
            else:
                content_en = "\n"
            html = template.format(
                title = data['title'],
                text = data['text'],
                content_en = content_en,
                h1 = data['h1'],
                google_counter=google_counter,
                yandex_counter=yandex_counter
                )

            html = html.replace('<!--google_counter-->',google_counter)
            html = html.replace('<!--yandex_counter-->',yandex_counter)
            filename = os.path.join(output_directory_path,'index.htm')

            with open(filename, "w", encoding='utf-8') as text_file:
                text_file.write(html)

        #sitemap

        with open(sitemap_path_manual, encoding='utf-8') as sitemap_manual:
                sitemap_template = sitemap_manual.read()


        with open(sitemap_path, "w", encoding='utf-8') as text_file:
            out = ''
            for page in pages2sitemap:
                out += "<url><loc>{url}</loc><lastmod>{lastmod}</lastmod><priority>{priority}</priority></url>\n".format(url=page['loc'],priority=page['priority'],lastmod=page['lastmod'])

            text_file.write(sitemap_template.replace('<!--GENERATED SITEMAP CONTENT FROM PYTHON-->',out))

if __name__ == "__main__":
    processor = Website_generator()
    #processor.generate()
    processor.generate(mode='standalone-full')