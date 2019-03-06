# -*- encoding: utf-8 -*-
"""
Hafas2GTFS

Usage:
  hafas2gtfs.py <input_dir> <output_dir> [--mapping=<mp>]
  hafas2gtfs.py -h | --help
  hafas2gtfs.py --version

Options:
  -h --help       Show this screen.
  --version       Show version.
  --mapping=<mp>  Map filenames

"""
import os
from datetime import datetime,timedelta

import csv
from pyproj import Proj
from bitstring import Bits


projector_utm = Proj(proj='utm', zone=32, ellps='WGS84')
projector_gk = Proj(proj='tmerc', ellps='bessel', lon_0='9d0E',
    lat_0='0', x_0='500000')


def convert_utm(x, y):
    lon, lat = projector_utm(x, y, inverse=True)
    return lon, lat


def convert_gk(x, y):
    lon, lat = projector_gk(x, y, inverse=True)
    return lon, lat


GTFS_FILES = (
    'agency.txt',
    'calendar.txt',
    'calendar_dates.txt',
    'routes.txt',
    'shapes.txt',
    'stop_times.txt',
    'stops.txt',
    'trips.txt',
)

GTFS_FILES = {
    'agency.txt': ('agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang', 'agency_phone'),
    'routes.txt': ('route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_desc', 'route_type', 'route_url', 'route_color', 'route_text_color'),
    'trips.txt': ('route_id', 'service_id', 'trip_id', 'trip_headsign', 'trip_short_name', 'direction_id', 'block_id', 'shape_id'),
    'stop_times.txt': ('trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'stop_headsign', 'pickup_type', 'drop_off_type', 'shape_dist_traveled'),
    'stops.txt': ('stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon', 'zone_id', 'stop_url', 'location_type', 'parent_station'),
    'calendar.txt': ('service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date'),
    'calendar_dates.txt': ('service_id', 'date', 'exception_type')
}

"""
    0 - Tram, Streetcar, Light rail. Any light rail or street level system within a metropolitan area.
    1 - Subway, Metro. Any underground rail system within a metropolitan area.
    2 - Rail. Used for intercity or long-distance travel.
    3 - Bus. Used for short- and long-distance bus routes.
    4 - Ferry. Used for short- and long-distance boat service.
    5 - Cable car. Used for street-level cable cars where the cable runs beneath the car.
    6 - Gondola, Suspended cable car. Typically used for aerial cable cars where the car is suspended from the cable.
    7 - Funicular. Any rail system designed for steep inclines.
"""

ROUTE_TYPES = {
  "AG" : 1,
  "ALS" : 2,
  "ALV"  : 4,
  "ARC" : 2,
  "ARZ"   : 1,
  "ATR"  : 2,
  "ATZ" : 1,
  "AVA"  : 4,
  "AVE"  : 2,
  "BAT"  : 4,
  "BAV" : 4,
  "BEX"  : 2,
  "BUS": 3,
  "CAT": 2,
  "CNL": 2,
  "D": 2,
  "E" : 1,
  "EC" : 2,
  "EM" : 2,
  "EN" : 2,
  "ES" : 2,
  "EST" : 2,
  "EXB" : 3,
  "EXT" : 1,
  "FAE" : 4,
  "FUN" : 6,
  "FYR" : 2,
  "GB" : 6,
  "GEX" : 2,
  "IC" : 2,
  "ICE" : 2,
  "ICN" : 2,
  "IN" : 2,
  "IR" : 2,
  "IRE" : 2,
  "JAT" : 1,
  "KAT"  : 4,
  "KB" : 3,
  "KUT" : 3,
  "LB" : 6,
  "M" : 0,
  "MP" : 0,
  "NFB" : 3,
  "NFO" : 3,
  "NFT" : 0,
  "NZ" : 2,
  "OEC" : 2,
  "OIC" : 2,
  "P" : 1,
  "R" : 2,
  "RB" : 2,
  "RE" : 2,
  "RJ" : 2,
  "RSB" : 1,
  "S" : 1,
  "SB" : 1,
  "SL" : 6,
  "SN" : 1,
  "STB" : 1,
  "SZ" : 1,
  "T" : 0,
  "TAL" : 2,
  "TGV": 2,
  "THA" : 2,
  "TLK": 2,
  "TRO" : 3,
  "TX" : 3,
  "UEX" : 1,
  "UUU" : 2,
  "VAE" : 2,
  "WB" : 1,
  "X" : 2,
  "X2" : 2,
  "ZUG" : 1,
}

ROUTE_COLORS = {
  "AG" : "ffea00",
  "ALS" : "",
  "ALV"  : "",
  "ARC" : "",
  "ARZ"   : "ffea00",
  "ATR"  : "",
  "ATZ" : "ffea00",
  "AVA"  : "",
  "AVE"  : "",
  "BAT"  : "",
  "BAV" : "",
  "BEX"  : "",
  "BUS": "",
  "CAT": "",
  "CNL": "",
  "D": "ff0000",
  "E" : "ffea00",
  "EC" : "ff0000",
  "EM" : "",
  "EN" : "ff0000",
  "ES" : "",
  "EST" : "",
  "EXB" : "",
  "EXT" : "ffea00",
  "FAE" : "",
  "FUN" : "",
  "FYR" : "",
  "GB" : "",
  "GEX" : "",
  "IC" : "ff0000",
  "ICE" : "ffffff",
  "ICN" : "ff0000",
  "IN" : "",
  "IR" : "ff8080",
  "IRE" : "ff8080",
  "JAT" : "ffea00",
  "KAT"  : "",
  "KB" : "ffea00",
  "KUT" : "",
  "LB" : "",
  "M" : "",
  "MP" : "",
  "NFB" : "",
  "NFO" : "",
  "NFT" : "",
  "NZ" : "",
  "OEC" : "",
  "OIC" : "",
  "P" : "ffea00",
  "R" : "",
  "RB" : "",
  "RE" : "",
  "RJ" : "",
  "RSB" : "ffea00",
  "S" : "ffea00",
  "SB" : "ffea00",
  "SL" : "",
  "SN" : "ffea00",
  "STB" : "ffea00",
  "SZ" : "ffea00",
  "T" : "ff8a00",
  "TAL" : "",
  "TGV": "",
  "THA" : "",
  "TLK": "",
  "TRO" : "",
  "TX" : "",
  "UEX" : "ffea00",
  "UUU" : "",
  "VAE" : "",
  "WB" : "ffea00",
  "X" : "",
  "X2" : "",
  "ZUG" : "ffea00",
}

ROUTE_TEXT_COLORS = {
  "AG" : "",
  "ALS" : "",
  "ALV"  : "",
  "ARC" : "",
  "ARZ"   : "",
  "ATR"  : "",
  "ATZ" : "",
  "AVA"  : "",
  "AVE"  : "",
  "BAT"  : "",
  "BAV" : "",
  "BEX"  : "",
  "BUS": "",
  "CAT": "",
  "CNL": "",
  "D": "F2F2F2",
  "E" : "",
  "EC" : "F2F2F2",
  "EM" : "",
  "EN" : "F2F2F2",
  "ES" : "",
  "EST" : "",
  "EXB" : "",
  "EXT" : "",
  "FAE" : "",
  "FUN" : "",
  "FYR" : "",
  "GB" : "",
  "GEX" : "",
  "IC" : "F2F2F2",
  "ICE" : "ff0000",
  "ICN" : "F2F2F2",
  "IN" : "",
  "IR" : "",
  "IRE" : "",
  "JAT" : "",
  "KAT"  : "",
  "KB" : "",
  "KUT" : "",
  "LB" : "",
  "M" : "",
  "MP" : "",
  "NFB" : "",
  "NFO" : "",
  "NFT" : "",
  "NZ" : "",
  "OEC" : "",
  "OIC" : "",
  "P" : "",
  "R" : "",
  "RB" : "",
  "RE" : "",
  "RJ" : "",
  "RSB" : "",
  "S" : "",
  "SB" : "",
  "SL" : "",
  "SN" : "",
  "STB" : "",
  "SZ" : "",
  "T" : "",
  "TAL" : "",
  "TGV": "",
  "THA" : "",
  "TLK": "",
  "TRO" : "",
  "TX" : "",
  "UEX" : "",
  "UUU" : "",
  "VAE" : "",
  "WB" : "",
  "X" : "",
  "X2" : "",
  "ZUG" : "",
}

DIRECTIONS = {
    '1': '0',
    '2': '1',
    'H': '0',
    'R': '1',
}


class Hafas2GTFS(object):
    def __init__(self, hafas_dir, out_dir, mapping=None):
        self.hafas_dir = hafas_dir
        self.out_dir = out_dir
        self.mapping = mapping
        self.route_counter = 0
        self.routes = {}

    def make_gtfs_files(self):
        self.files = {}
        for gtfs_file, columns in GTFS_FILES.items():
            file = open(os.path.join(self.out_dir, gtfs_file), 'w', newline='',
                        encoding='utf8')
            self.files[gtfs_file] = csv.DictWriter(
                file,
                columns,
            )
            self.files[gtfs_file].writeheader()

    def get_path(self, name):
        return os.extsep.join([os.path.join(self.hafas_dir, name), 'txt'])

    def get_name(self, name):
        if self.mapping is None:
            return name
        return self.mapping.get(name, name)

    def create(self):
        self.make_gtfs_files()
        self.parse_bfkoord_geo()
        self.service_id = self.parse_eckdaten()
        self.infotext = self.parse_infotext()
        self.parse_bitfield()
        self.write_servicedates()
        self.agency_id = self.write_agency()
        self.parse_fplan()

    def write_agency(self):
        self.agency_id = '1'
        self.files['agency.txt'].writerow({
            'agency_id': self.agency_id,
            'agency_name': 'Agency Name',
            'agency_url': '',
            'agency_timezone': '',
            'agency_lang': '',
            'agency_phone': ''
        })
        return self.agency_id

    def write_servicedates(self):
        self.files['calendar.txt'].writerow({
            'service_id': "000000",
            'monday' : '1',
            'tuesday' : '1',
            'wednesday' : '1',
            'thursday' : '1',
            'friday' : '1',
            'saturday' : '1',
            'sunday' : '1',
            'start_date' : self.start.strftime('%Y%m%d'),
            'end_date' : self.end.strftime('%Y%m%d')
        })
        for service_id,bitfield in self.services.items():
            y = str(bitfield.bin)
            for z in range(0, len(y)):
                if y[z] == '1':
                    date = (self.start + timedelta(days=z))
                    self.files['calendar_dates.txt'].writerow({
                        'service_id': service_id,
                        'date': date.strftime('%Y%m%d'),
                        'exception_type' : 1})
        return None

    def write_route(self, meta):
        route_id = meta.get('line_number')
        if route_id is None:
            self.route_counter += 1
            route_id = self.route_counter
        if route_id in self.routes:
            return self.routes[route_id]
        self.routes[route_id] = route_id
        self.files['routes.txt'].writerow({
            'route_id': route_id,
            'agency_id': self.agency_id,
            'route_short_name': meta['mean_of_transport'],
            'route_long_name': (meta['mean_of_transport']  + " " if meta['trainnumber'].isdigit() else "") + meta['trainnumber'],
            'route_desc': '',
            'route_type': str(ROUTE_TYPES.get(meta['mean_of_transport'], 0)),
            'route_url': '',
            'route_color': ROUTE_COLORS.get(meta['mean_of_transport'], "000000"),
            'route_text_color': ROUTE_TEXT_COLORS.get(meta['mean_of_transport'], "000000")
        })
        return route_id

    def write_trip(self, route_id, service_id, meta, tripid):
        self.files['trips.txt'].writerow({
            'route_id': route_id,
            'service_id': service_id,
            'trip_id': tripid,
            'trip_headsign': meta['headsign'],
            'trip_short_name': meta['trainnumber'],
            'direction_id': meta.get('direction', '0'),
            'block_id': '',
            'shape_id': ''
        })
        return tripid

    def get_gtfs_time(self, time):
        if time is None:
            return None
        time = list(time)
        if len(time) == 2:
            time = time + ['00']
        time = [str(t).zfill(2) for t in time]
        return ':'.join(time)

    def write_stop(self, stop_line):
        self.files['stops.txt'].writerow({
            'stop_id': stop_line['stop_id'],
            'stop_code': stop_line['stop_id'],
            'stop_name': stop_line['stop_name'],
            'stop_desc': '',
            'stop_lat': stop_line['stop_lat'],
            'stop_lon': stop_line['stop_lon'],
            'zone_id': None,
            'stop_url': '',
            'location_type': '0',  # FIXME
            'parent_station': None
        })
        return stop_line['stop_id']

    def write_stop_time(self, trip_id, stop_sequence, stop_line):
        stop_id = stop_line['stop_id']

        arrival_time = self.get_gtfs_time(stop_line['arrival_time'])
        departure_time = self.get_gtfs_time(stop_line['departure_time'])

        if not arrival_time and departure_time:
            arrival_time = departure_time
        elif not departure_time and arrival_time:
            departure_time = arrival_time

        self.files['stop_times.txt'].writerow({
            'trip_id': trip_id,
            'arrival_time': arrival_time,
            'departure_time': departure_time,
            'stop_id': stop_id,
            'stop_sequence': stop_sequence,
            'stop_headsign': '',
            'pickup_type': '0',
            'drop_off_type': '0',
            'shape_dist_traveled': ''
        })

    def parse_eckdaten(self):
        contents = open(self.get_path(self.get_name('ECKDATEN'))).read()
        data = contents.splitlines()
        self.start = datetime.strptime(data[0], '%d.%m.%Y')
        self.end = datetime.strptime(data[1], '%d.%m.%Y')
        self.name = data[1]

    def parse_bfkoord_geo(self):
        for line in open(self.get_path(self.get_name('BFKOORD_GEO')),
                         encoding='iso-8859-1'):
            bla = {
              'stop_id': int(line[:8]),
              'stop_lon': line[8:17].strip(),
              'stop_lat': line[19:28].strip(),
              'stop_name': line[39:].strip()
            }
            self.write_stop(bla)


    def parse_bitfield(self):
        self.services = {}
        for line in open(self.get_path(self.get_name('BITFELD'))):
            service_id = line[:6]
            # "For technical reasons 2 bits are inserted directly
            # before the first day of the start of the timetable period
            # and two bits directly after the last day at the end of the
            # timetable period."
            self.services[service_id] = Bits(hex=line[6:])[2:]

    def parse_infotext(self):
        infotext = {}
        for line in open(self.get_path(self.get_name('INFOTEXT_DE')),
                         encoding='iso-8859-1'):
            infotext[line[0:7]] = line[8:].strip()

        return infotext

    def parse_fplan(self):
        state = 'meta'
        meta = {}
        linenumber = 0
        curtripid = 0
        service_id = 0
        for line in open(self.get_path(self.get_name('FPLAN')),
                         encoding='latin1'):
            linenumber = linenumber +1
            if line.startswith('%'):
                continue
            if line.startswith('*'):
                if not state == 'meta':
                    if meta != {}:
                        self.write_trip(route_id, service_id, meta, curtripid)
                        meta = {}
                state = 'meta'
                meta.update(self.parse_fplan_meta(line))
                if line.startswith('*Z'):
                    curtripid += 1
            else:
                if not state == 'data':
                    state = 'data'
                    stop_sequence = 0
                    route_id = self.write_route(meta)
                    service_id = meta['service_id']
                    if service_id == "": service_id = "000000"
                stop_sequence += 1
                stop_line_info = self.parse_schedule(line)
                self.write_stop_time(curtripid, stop_sequence, stop_line_info)
                meta['headsign'] = stop_line_info['stop_name']

    def parse_schedule(self, line):
        """
0000669 Refrath                   0635
        """
        return {
            'stop_id': int(line[:7]),
            'stop_name': line[8:30].strip(),
            'arrival_time': self.parse_time(line[31:35]),
            'departure_time': self.parse_time(line[38:42])
        }

    def parse_time(self, time_str):
        time_str = time_str.strip()
        if not time_str:
            return None
        #print time_str
        # TODO: include seconds if present
        return (int(time_str[0:2]), int(time_str[2:4]))

    def parse_fplan_meta(self, line):
        if hasattr(self, 'parse_fplan_meta_%s' % line[1]):
            return getattr(self, 'parse_fplan_meta_%s' % line[1])(line)
        return {}

    def parse_fplan_meta_Z(self, line):
        return {
            'trainnumber' : str(int(line[3:8])),
            'line_number': line[3:8] + "." + line[9:15],
            'service_number': line[3:8] + "." + line[9:15] + "." + line[18:21],
            'administration': line[9:15],
            'number_intervals': line[22:25],
            'time_offset': line[26:29]
        }

    def parse_fplan_meta_G(self, line):
        return {
            'mean_of_transport': line[3:6].strip()
        }

    def parse_fplan_meta_A(self, line):
        # discern A und A VE
        return {
          'service_id' : line[22:28].strip()
        }

    def parse_fplan_meta_A(self, line):
        # discern A und A VE
        return {
          'service_id' : line[22:28].strip()
        }

    def parse_fplan_meta_I(self, line):
        code = line[3:5]
        nr = line[29:36]
        text = self.infotext[nr].strip()
        if code == "ZN" or code == "RN":
            return {'trainnumber' : text}
        return {}

    def parse_fplan_meta_L(self, line):
        return {
          'trainnumber' : line[3:12].strip()
        }

    def parse_fplan_meta_R(self, line):
        direction = line[3:4].strip()
        direction = DIRECTIONS.get(direction, direction)
        return {
            'direction': direction
        }


def main(hafas_dir, out_dir, options=None):
    if options is None:
        options = {}
    config = {}
    if options.get('--mapping'):
        config['mapping'] = dict([o.split(':') for o in options.get(
                                 '--mapping').split(',')])
    h2g = Hafas2GTFS(hafas_dir, out_dir, **config)
    h2g.create()

if __name__ == '__main__':
    from docopt import docopt

    arguments = docopt(__doc__, version='Hafas2GTFS 0.0.1')
    main(arguments['<input_dir>'], arguments['<output_dir>'], options=arguments)
