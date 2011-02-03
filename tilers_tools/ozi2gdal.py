#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 2011-01-27 11:33:43 

###############################################################################
# Copyright (c) 2010, Vadim Shlyakhov
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#******************************************************************************

import os
import logging
import locale
from optparse import OptionParser

from tiler_functions import *
    
datum_map={ 
    # http://www.hemanavigator.com.au/Products/TopographicalGPS/OziExplorer/tabid/69/Default.aspx
    'WGS 84':
        '+datum=WGS84',
    'WGS 72': # http://www.linz.govt.nz/docs/miscellaneous/transformation-parameters-chathamislands.pdf
        '+ellps=WGS72 +towgs84=0,0,4.5,0,0,0.554,0.2263',
    'NAD83':
        '+datum=NAD83',
    'European 1950':
        #'+towgs84=-84.0000,-97.0000,-117.0000 +ellps=intl',
        # http://trac.osgeo.org/proj/ticket/32
        '+towgs84=+towgs84=-87,-98,-121 +ellps=intl', 
    'European 1950 (Mean France)':
        '+towgs84=+towgs84=-87,-98,-121 +ellps=intl', 
    'European 1950 (Spain and Portugal)':
        '+towgs84=+towgs84=-84,-107,-120 +ellps=intl', 
    'European 1950 (Greece)':
        '+towgs84=+towgs84=-84,-95,-130 +ellps=intl', 
    'Geodetic Datum 1949':
        '+datum=nzgd49',
    'Ireland 1965':
        '+datum=ire65',
    'Hermannskogel':
        '+datum=hermannskogel',
    'Potsdam Rauenberg DHDN':
        '+datum=potsdam',
    'GGRS87':
        '+datum=GGRS87',
    'EGSA87':
        '+datum=GGRS87',
    'Rome 1940':
        '+towgs84=-104.1,-49.1,-9.9,0.971,-2.917,0.714,-11.68 +ellps=intl',
    'Pulkovo 1942 (1)': # http://trac.osgeo.org/gdal/ticket/3176
        '+ellps=krass +towgs84=23.9,-141.3,-80.9,0,-0.37,-0.85,-0.12', 
    'Pulkovo 1942 (2)':
        '+ellps=krass +towgs84=23.9,-141.3,-80.9,0,-0.37,-0.85,-0.12', 
    'Pulkovo 1942': # http://ne-grusti.narod.ru/oziexplorer.html
        '+ellps=krass +towgs84=23.9,-141.3,-80.9,0,-0.37,-0.85,-0.12', 
    'Australian Geodetic 1966': # http://www.osgeo.org/pipermail/gdal-dev/2006-February/008090.html
        '+ellps=aust_SA +towgs84=-129.193,-41.212,130.73,-0.246,-0.374,-0.329,-2.955',
    'Australian Geodetic 1984':
        '+ellps=aust_SA +towgs84=-117.763,-51.51,139.061,-0.292,-0.443,-0.277,-0.191',
    'Australian Geocentric 1994 (GDA94)':
        '+ellps=GRS80 +towgs84=0,0,0,0,0,0,0',
    'Ord Srvy Grt Britn':
        '+towgs84=446.448,-125.157,542.060,0.1502,0.2470,0.8421,-20.4894 +ellps=airy',
    'OSGB 36':
        '+towgs84=446.448,-125.157,542.060,0.1502,0.2470,0.8421,-20.4894 +ellps=airy',
    'Finland Hayford':
        #'+towgs84=-90.7,-106.1,-119.2,4.09,0.218,-1.05,1.37 +ellps=intl', # see esri:4123
        '+towgs84=-78.00,-231.00,-97.00 +ellps=intl',
    'RT 90': # http://www.lantmateriet.se/templates/LMV_Page.aspx?id=4766&lang=EN
        '+towgs84=414.0978567149,41.3381489658,603.0627177516,-0.8550434314,2.1413465185,-7.0227209516,0 +ellps=bessel', # http://sv.wikipedia.org/wiki/RT_90
    #Datum Lisboa (Portugal), 29, -304.046, -60.576, 103.640
    #European 1950 (Portugal), 14, -87.987, -108.639, -121.593

    #'Carthage CH-1903':
        #'+datum=carthage',    
    # European 1979
    # NTF France
    # Norsk
    # Rijksdriehoeksmeting
    # Observatorio 1966
    # S42
    }

def dms2dec(degs=0,mins=0,ne='E',sec=0):
    return (float(degs)+float(mins)/60+float(sec)/3600)*(-1 if ne in ('W','S') else 1 )

proj_map={
    'Latitude/Longitude':                       '+proj=latlong',
    'Mercator':                                 '+proj=merc',
    'Transverse Mercator':                      '+proj=tmerc',
    '(UTM) Universal Transverse Mercator':      '+proj=utm',
    '(BNG) British National Grid':              '+init=epsg:27700', # not tested
    '(IG) Irish Grid':                          '+init=epsg:29902', # not tested
    '(NZG) New Zealand Grid':                   '+init=epsg:27200', # not tested
    '(SG) Swedish Grid': # http://www.fig.net/pub/fig2006/papers/ps05_03/ps05_03_04_engberg_lilje_0670.pdf
        '+proj=tmerc +lon_0=15.808277777778 +x_0=1500000 +y_0=0', # http://en.wikipedia.org/wiki/Swedish_grid
    '(SUI) Swiss Grid':                         '+init=epsg:21781', # not tested
    '(I) France Zone I':                        '+init=epsg:27571', # not tested
    '(II) France Zone II':                      '+init=epsg:27572', # not tested
    '(III) France Zone III':                    '+init=epsg:27573', # not tested
    '(IV) France Zone IV':                      '+init=epsg:27574', # not tested
    'Lambert Conformal Conic':                  '+proj=lcc',
    '(A)Lambert Azimuthual Equal Area':         '+proj=laea',       # not tested
    '(EQC) Equidistant Conic':                  '+proj=eqdc',
    'Sinusoidal':                               '+proj=sinu',       # not tested
    'Polyconic (American)':                     '+proj=poly',
    'Albers Equal Area':                        '+proj=aea',        # not tested
    'Van Der Grinten':                          '+proj=vandg',      # not tested
    'Vertical Near-Sided Perspective':          '+proj=nsper',      # not tested
    '(WIV) Wagner IV':                          '+proj=wag4',       # not tested
    'Bonne':                                    '+proj=bonne',      # not tested
    '(MT0) Montana State Plane Zone 2500':      '+init=esri:102300',# not tested
    '(ITA1) Italy Grid Zone 1': # http://mpa.itc.it/markus/shortcourse/notes2.html
        '+init=epsg:26591 +towgs84=-85.88,-28.85,+49.67,-1.003,-2.383,-1.808,-27.82', # not tested
    '(ITA2) Italy Grid Zone 2':
        '+init=epsg:26592 +towgs84=-85.88,-28.85,+49.67,-1.003,-2.383,-1.808,-27.82', # not tested
    '(VICMAP-TM) Victoria Aust.(pseudo AMG)': # http://www.gpsoz.com.au/VicRoadsInfo.htm
        '+proj=tmerc +lat_0=145 +x_0=500000 +y_0=10000000',         # not tested
    '(VICGRID) Victoria Australia':             '+init=epsg:3110',  # not tested
    '(VG94) VICGRID94 Victoria Australia':      '+init=epsg:3111',  # not tested
    'Gnomonic':                                 '+proj=gnom',
    }
parm_map=( 
    '+lat_0=', # 1. Latitude Origin
    '+lon_0=', # 2. Longitude Origin
    '+k=',     # 3. K Factor
    '+x_0=',   # 4. False Easting
    '+y_0=',   # 5. False Northing
    '+lat_1=', # 6. Latitude 1
    '+lat_2=', # 7. Latitude 2
    '+h=',     # 8. Height - used in the Vertical Near-Sided Perspective Projection
               # 9. Sat - not used
               #10. Path - not used
    )

def hdr_parms(hdr, patt): 
    'filter header for params starting with "patt"'
    return [i for i in hdr if i[0].startswith(patt)]
    
def hdr_read(map_file): 
    'read map header'
    header=[[i.strip() for i in l.split(',')] for l in open(map_file, 'rU')]
    if not (header and header[0][0].startswith('OziExplorer Map Data File')): 
        raise Exception("*** invalid file: %s" % map_file)
    ld(header)
    return header

def srs_refs(hdr):
    'returns srs for the map projection and srs for the REF points'
    refs=[i for i in hdr_parms(hdr, 'Point') if i[2] != ''] # Get a list of geo refs
    if options.srs:
        return(options.srs,refs)
    if options.proj:
        proj=options.proj
    else:
        proj_id=hdr_parms(hdr, 'Map Projection')[0][1]
        parm_lst=hdr_parms(hdr, 'Projection Setup')[0]
        try:
            proj=[proj_map[proj_id]]
        except KeyError: 
            raise Exception("*** Unsupported projection (%s)" % proj_id)
        if '+proj=' in proj[0]: # overwise assume it already has a full data defined
            # get projection parameters
            parms=[ i[0]+i[1] for i in zip(parm_map,parm_lst[1:]) if i[1].translate(None,'0.')]
            if '+proj=utm' in proj[0]:
                if refs[0][7] == '': # refs are cartesian with a zone defined
                    parms.append('+zone='+refs[0][13])
                    if refs[0][16] != 'N': 
                        parms.append('+south')
                else: # refs are lat/long, then find zone, hemisphere
                    # doesn't seem to have central meridian for UTM
                    zone=(dms2dec(*refs[0][9:12]) + 3 % 360) // 6 + 30
                    parms.append('+zone=%d' % zone)
                    if refs[0][8] != 'N': 
                        parms.append('+south')
            if parms:
                proj.extend(parms)
            # setup a central meridian artificialy to allow charts crossing meridian 180
            leftmost=min(refs,key=lambda r: r[2])
            rightmost=max(refs,key=lambda r: r[2])
            ld('leftmost',leftmost,'rightmost',rightmost)
            if leftmost[4] > rightmost[4] and '+lon_0=' not in proj[0]:
                proj.append(' +lon_0=%i' % int(leftmost[9]))
    datum_id=hdr[4][0]
    dtm=[0,0]
    logging.info('\t%s, %s' % (datum_id,proj_id))
    if options.datum: 
        datum=options.datum
    elif datum_id.startswith('Auto Shift'):
        ld(hdr[4])
        dtm=map(lambda x:float(x)/3600,hdr[4][2:4])
        datum='WGS84'
    else:
        datum_id=hdr[4][0]
        try:
            datum=datum_map[datum_id] 
        except KeyError: 
            raise Exception("*** Unsupported datum (%s)" % datum_id)
    srs=' '.join(proj)+' '+datum+' +nodefs'
    ld(srs)
    return srs,refs,dtm

def find_image(img_path, map_dir, map_fname):
    imp_path_slashed=img_path.replace('\\','/') # get rid of windows separators
    imp_path_lst=os.path.split(imp_path_slashed)
    img_fname=imp_path_lst[-1]
    try_enc=(locale.getpreferredencoding(),'utf_8','iso-8859-1','iso-8859-2','cp1251')
    match_patt=[img_fname.decode(i,'ignore').lower() for i in try_enc]
    img_hyb=os.path.splitext(map_fname)[0]+os.path.splitext(img_fname)[1]
    match_patt.append(img_hyb.lower())
    dir_lst=[i.decode(try_enc[0],'ignore') for i in os.listdir(map_dir if map_dir else '.')]
    ld((match_patt,dir_lst))
    match=[i for i in dir_lst if i.lower() in match_patt]
    try:
        ld(map_dir, match)
        return os.path.join(map_dir, match[0])
    except IndexError: 
        raise Exception("*** Image file not found: %s" % img_path)

gmt_templ='''# @VGMT1.0 @GPOLYGON
# @Jp"%s"
# FEATURE_DATA
>
# @P
%s'''

def cut_poly(hdr,out_dataset,out_srs,dtm):
#    size=[i for i in gdalinfo.splitlines() if 'Size is' in i][0][len('Size is'):].split(',')
#    (width, height)=[i.strip() for i in size]
    width,height=map(int,hdr_parms(hdr, 'IWH')[0][2:])
    ld((width, height))
    mmpxy=[map(int,i[2:]) for i in hdr_parms(hdr, 'MMPXY')]   # Moving Map border pixels
    mmpll=[map(float,i[2:]) for i in hdr_parms(hdr, 'MMPLL')] # Moving Map border lat,lon
    inside=[i for i in mmpxy # check if MMP polygon is inside the image border
        if not ((i[0] == 0 or i[0] == width) and (i[1] == 0 or i[1] == height))]
    if not inside:
        return '',''
    # create polygon
    poly_pix=['%d %d' % tuple(i) for i in mmpxy]
    poly='POLYGON(('+','.join(poly_pix)+'))' # Create cutline

    # convert cutline geo coordinates to the chart's srs
    if dtm != [0,0]:
        # alter points as per DTM values
        mmpll=[(i[0]+dtm[0],i[1]+dtm[1]) for i in mmpll]
    inp = '\n'.join(['%r %r' % tuple(i) for i in mmpll])
    poly_xy=command(['gdaltransform','-s_srs','+proj=longlat','-t_srs',out_srs], inp)

#    out=command(['gdaltransform','-s_srs',out_dataset,'-t_srs',out_srs], '\n'.join(poly_pix))
    return poly, gmt_templ % (out_srs,poly_xy)

def dest_path(src,dest_dir,ext='',template='%s'):
    src_dir,src_file=os.path.split(src)
    base,sext=os.path.splitext(src_file)
    dest=(template % base)+ext
    if not dest_dir:
        dest_dir=src_dir
    if dest_dir:
        dest='%s/%s' % (dest_dir,dest)
    ld(base,dest)
    return dest

class Opt(object):
    def __init__(self,**dictionary):
        self.dict=dictionary
    def __getattr__(self, name):
        return self.dict.setdefault(name,None)
        
def map2vrt(map_file,dest=None,options=None):
    map_file=map_file.decode(locale.getpreferredencoding(),'ignore')
    hdr=hdr_read(map_file)      # Read map header
    img_file=find_image(hdr[2][0],*os.path.split(map_file))


    if dest:
        base=os.path.split(dest)[0]
    else:
        base=dest_path(img_file,options.dest_dir)
    dest_dir=os.path.split(base)[0]
    img_path=os.path.relpath(img_file,dest_dir)
    out_dataset= os.path.basename(base+'.vrt') # output VRT file    
    logging.info(' %s : %s -> %s' % (map_file,img_file,out_dataset))

    out_srs,refs,dtm=srs_refs(hdr)
    if refs[0][14] != '': # refs are cartesian
        refs_proj=[i[14:16]for i in refs]
    else: # refs are lat/long
        lonlat=[(dms2dec(*i[9:12]), dms2dec(*i[6:9])) for i in refs]
        if dtm != [0,0]:
            ld(lonlat, 'dtm',dtm)
            lonlat=[(i[0]+dtm[0],i[1]+dtm[1]) for i in lonlat]
            ld(lonlat)
        if out_srs.startswith('+proj=latlong'):
            refs_proj=lonlat
        else: # reproject coordinates
            inp = '\n'.join(['%r %r' % i for i in lonlat])
            refs_out=command(['gdaltransform','-s_srs','+proj=longlat','-t_srs',out_srs], inp)
            refs_proj=[ i.split() for i in refs_out.splitlines()]
    if len(refs) == 2:
        logging.warning(' Only 2 reference points: assuming the chart is north alligned')
        refs.append(['','',refs[0][2],refs[1][3]])
        refs_proj.append([refs_proj[0][0],refs_proj[1][1]])
    ld('refs',refs)
    ld('refs_proj',refs_proj)
    gcps=flatten([('-gcp', i[0][2],i[0][3],i[1][0],i[1][1]) for i in zip(refs, refs_proj)])
    transl_cmd=['gdal_translate','-of','VRT',img_path,out_dataset,'-a_srs', out_srs]
    if options.expand:
        transl_cmd=transl_cmd+['-expand',options.expand]
    try:
        cdir=os.getcwd()
        if dest_dir:
            os.chdir(dest_dir)
        command(transl_cmd + gcps)
        poly,gmt_data=cut_poly(hdr,out_dataset,out_srs,dtm)
    finally:
        os.chdir(cdir)

    if options.get_cutline: # print cutline then return
        print poly
        return
    if gmt_data and not options.no_cut_file: # create shapefile with a cut polygon
        f=open(base+'.gmt','w+')
        f.write(gmt_data)
        f.close()

def proc_src(src):
    map2vrt(src,options=options)

if __name__=='__main__':
    usage = "usage: %prog [--cut] [--dest-dir=DEST_DIR] MAP_file..."
    parser = OptionParser(usage=usage,
        description="Converts OziExplorer's .MAP file into GDAL .VRT format")
    parser.add_option("-d", "--debug", action="store_true", dest="debug")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet")
    parser.add_option("-t", "--dest-dir", dest="dest_dir", default='',
        help='destination directory (default: current)')
    parser.add_option("--no-data", dest="no_data", default='',
        help='set nodata masking values for input bands, separated by commas')
    parser.add_option("--expand", choices=('gray','rgb','rgba'),
        help='expose a dataset with 1 band with a color table as a dataset with 3 (RGB) or 4 (RGBA) bands')
    parser.add_option("--of",  default='VRT',
        help='Select the output format. The default is VRT')
    parser.add_option("--no-cut-file", action="store_true", 
        help='do not create a file with a cutline polygon from KAP file')
    parser.add_option("--get-cutline", action="store_true", 
        help='print cutline polygon from KAP file then exit')
    parser.add_option("--srs", default=None,
        help='override full chart with PROJ.4 definition of the spatial reference system')
    parser.add_option("--datum", default=None,
        help="override chart's datum (PROJ.4 definition)")
    parser.add_option("--proj", default=None,
        help="override chart's projection (BSB definition)")

    (options, args) = parser.parse_args()
    if not args:
        parser.error('No input file(s) specified')
    logging.basicConfig(level=logging.DEBUG if options.debug else 
        (logging.ERROR if options.quiet else logging.INFO))

    ld(os.name)
    ld(options)

    map(proc_src,args)

