#!/usr/bin/python
# Imports tiger data from the table provided on the command-line into the tracker tables.

from django.core.management.base import BaseCommand
from optparse import make_option, OptionParser
from tracker.models import *

class Tiger(models.Model):
    gid = models.IntegerField(primary_key=True)
    statefp = models.CharField(max_length=2)
    countyfp = models.CharField(max_length=3)
    countyns = models.CharField(max_length=8)
    tlid = models.IntegerField()
    tfidl = models.IntegerField()
    tfidr = models.IntegerField()
    mtfcc = models.CharField(max_length=5)
    fullname = models.CharField(max_length=100)
    smid = models.CharField(max_length=22)
    lfromadd = models.CharField(max_length=12)
    ltoadd = models.CharField(max_length=12)
    rfromadd = models.CharField(max_length=12)
    rtoadd = models.CharField(max_length=12)
    zipl = models.CharField(max_length=5)
    zipr = models.CharField(max_length=5)
    featcat = models.CharField(max_length=1)
    hydroflg = models.CharField(max_length=1)
    railflg = models.CharField(max_length=1)
    roadflg = models.CharField(max_length=1)
    olfflg = models.CharField(max_length=1)
    passflg = models.CharField(max_length=1)
    divroad = models.CharField(max_length=1)
    ttyp = models.CharField(max_length=1)
    deckedroad = models.CharField(max_length=1)
    artpath = models.CharField(max_length=1)
    the_geom = models.GeometryField()

countyfp_to_borough = {'061' : 'Manhattan'}

class Command(BaseCommand):
    help = "Imports tiger data from the table provided into the tracker tables."

    def handle(self, tiger_table_name, **kw):

        Tiger._meta.db_table = tiger_table_name

        tiger_segs = Tiger.objects.filter(roadflg='Y')

         print "Importing from tiger data.  %d road segments to import" % len(tiger_segs)
         for i, tiger_seg in enumerate(tiger_segs):
             borough = countyfp_to_borough[tiger_seg.countyfp]
             if i and i % 500 == 0:
                 print "finished %d" % i
             if not tiger_seg.fullname:
                 continue #riding through the city on a road with no name...

             road = Road(name = tiger_seg.fullname + ", " + borough)
             road.save()
             seg = RoadSegment(gid=tiger_seg.gid, geometry=tiger_seg.the_geom, road=road, path_order=-1)
             seg.save() 

        #now, set path order for each road

        for road in Road.objects.all():
            road_geometry = None
            segments = list(road.roadsegment_set.all())
            for segment in segments:
                if road_geometry:
                    road_geometry = road_geometry.union(segment.geometry)
                else: 
                    road_geometry = segment.geometry

            extent = road_geometry.extent
            x_extent = abs(road_geometry.extent[0] - road_geometry.extent[2])
            y_extent = abs(road_geometry.extent[1] - road_geometry.extent[3])
            
            if x_extent > y_extent:
                segments.sort(key=lambda segment:segment.geometry.extent[0])
            else:
                segments.sort(key=lambda segment:segment.geometry.extent[1])

            #and god help you if your road loops back on itself

            for i, segment in enumerate(segments):
                segment.path_order = i
                segment.save()
            