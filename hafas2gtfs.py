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


GTFS_FILES = {
    'agency.txt': ('agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang', 'agency_phone'),
    'routes.txt': ('route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_desc', 'route_type', 'route_url', 'route_color', 'route_text_color'),
    'trips.txt': ('route_id', 'service_id', 'trip_id', 'trip_headsign', 'trip_short_name', 'direction_id', 'block_id', 'shape_id', 'trip_code', 'info_text', 'hafas_trip_id'),
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
from collections import namedtuple


class ServiceTrip:
    def __init__(self, no, begin, end, begin_time=None, end_time=None):
        self.no = no
        self.begin = begin
        self.end = end
        self.begin_time = begin_time
        self.end_time = end_time

    def __repr__(self):
        return self.no


class Agency:
    def __init__(self, code, mode, agency_id, agency_name, agency_code):
        self.code = code
        self.mode = mode
        self.agency_id = agency_id
        self.agency_name = agency_name
        self.agency_code = agency_code
        self.routes = []

    def __repr__(self):
        return self.agency_name


class Hafas2GTFS(object):
    def __init__(self, hafas_dir, out_dir, mapping=None):
        self.hafas_dir = hafas_dir
        self.out_dir = out_dir
        self.mapping = mapping
        self.route_counter = 0
        self.routes = {}
        self.service_id_new = 0

    def make_gtfs_files(self):
        self.files = {}
        for gtfs_file, columns in GTFS_FILES.items():
            file = open(os.path.join(self.out_dir, gtfs_file), 'w', newline='',
                        encoding='utf8')
            writer = csv.DictWriter(
                file,
                columns,
            )
            writer.file = file
            self.files[gtfs_file] = writer
            writer.writeheader()

    def close(self):
        for writer in self.files.values():
            writer.file.close()

    def get_path(self, name):
        return os.extsep.join([os.path.join(self.hafas_dir, name), 'txt'])

    def get_name(self, name):
        if self.mapping is None:
            return name
        return self.mapping.get(name, name)

    def create(self):
        self.make_gtfs_files()
        self.parse_betreiber()
        self.parse_bfkoord_geo()
        self.service_id = self.parse_eckdaten()
        self.infotext = self.parse_infotext()
        self.parse_bitfield()
        self.parse_fplan()
        self.write_servicedates()
        self.write_agency()
        self.close()

    def write_agency(self):
        writer = self.files['agency.txt']
        #  add default agency
        for agency in self.agencies.values():
            writer.writerow({
            'agency_id': agency.agency_id,
            'agency_name': agency.agency_name,
            'agency_url': '',
            'agency_timezone': '',
            'agency_lang': '',
            'agency_phone': ''
        })

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
        trip_code = meta.get('trip_no')
        administration = meta['administration']
        agency_id = self.line2agency.get(administration)
        if not agency_id:
            agency = self.agencies.get(administration)
            if not agency:
                agency = self.add_agency(betreiber=administration,
                                agency_id=administration,
                                mode='',
                                agency_name=administration,
                                unique=False)
            agency_id = agency.agency_id
            self.line2agency[administration] = administration
        if trip_code:
            route_id = f'{agency_id}_{trip_code}'
        else:
            route_id = agency_id
        if route_id is None:
            self.route_counter += 1
            route_id = self.route_counter
        if route_id in self.routes:
            return self.routes[route_id]
        self.routes[route_id] = route_id

        self.files['routes.txt'].writerow({
            'route_id': route_id,
            'agency_id': agency_id,
            'route_short_name': meta['mean_of_transport'],
            'route_long_name': (meta['mean_of_transport']  + " "
                                if meta['trainnumber'].isdigit() else "") + meta['trainnumber'],
            'route_desc': '',
            'route_type': str(ROUTE_TYPES.get(meta['mean_of_transport'], 0)),
            'route_url': '',
            'route_color': ROUTE_COLORS.get(meta['mean_of_transport'], "000000"),
            'route_text_color': ROUTE_TEXT_COLORS.get(meta['mean_of_transport'], "000000"),
        })
        self.route_id = route_id

    def write_trip(self, service_id, meta):
        trip_code = meta.get('trip_no') or meta.get('trainnumber')
        info_text = meta.get('info_text', '')
        self.files['trips.txt'].writerow({
            'route_id': self.route_id,
            'service_id': service_id,
            'trip_id': self.trip_id,
            'trip_headsign': meta['headsign'],
            'trip_short_name': meta['trainnumber'],
            'direction_id': meta.get('direction', '0'),
            'block_id': '',
            'shape_id': '',
            'trip_code': trip_code,
            'info_text': info_text,
            'hafas_trip_id': self.hafas_trip_id,
        })

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

    def write_stop_time(self, stop_sequence, stop_line):
        stop_id = stop_line['stop_id']

        arrival_time = self.get_gtfs_time(stop_line['arrival_time'])
        departure_time = self.get_gtfs_time(stop_line['departure_time'])

        if not arrival_time and departure_time:
            arrival_time = departure_time
        elif not departure_time and arrival_time:
            departure_time = arrival_time

        self.files['stop_times.txt'].writerow({
            'trip_id': self.trip_id,
            'arrival_time': arrival_time,
            'departure_time': departure_time,
            'stop_id': stop_id,
            'stop_sequence': stop_sequence,
            'stop_headsign': '',
            'pickup_type': '0',
            'drop_off_type': '0',
            'shape_dist_traveled': '',
        })

    def parse_eckdaten(self):
        contents = open(self.get_path(self.get_name('ECKDATEN'))).read()
        data = contents.splitlines()
        self.start = datetime.strptime(data[0], '%d.%m.%Y')
        self.end = datetime.strptime(data[1], '%d.%m.%Y')
        self.name = data[1]

    def parse_betreiber(self):
        """Parse the agencies"""
        self.agencies = {}
        self.agency_ids = {}
        self.line2agency = {}
        self.agency_code_suffix = {}
        for line in open(self.get_path(self.get_name('BETRIEB')),
                         encoding='iso-8859-1'):
            betreiber = line[:5]
            agency_id = line[17:20].strip()
            agency = self.agencies.get(betreiber)
            if not agency:
                mode = line[9:12]
                agency_name = line[25:].strip().strip("'")
                agency = self.add_agency(betreiber, agency_id,
                                         mode, agency_name)
            else:
                routes = line[8:].strip().split(' ')
                agency.routes.extend(routes)
                for route in routes:
                    self.line2agency[route] = agency.agency_id

    def add_agency(self, betreiber, agency_id, mode, agency_name, unique=True):
        agency = Agency(code=betreiber,
                        mode=mode,
                        agency_id=agency_id,
                        agency_name=agency_name,
                        agency_code=agency_id)
        if unique:
            self.make_agency_id_unique(agency, agency_id)
        self.agencies[betreiber] = agency
        self.agency_ids[agency.agency_id] = None
        return agency

    def make_agency_id_unique(self, agency, agency_id):
        # append number, if agency_id already exists
        if agency.agency_id in self.agency_ids:
            agency_code_suffix = self.agency_code_suffix.get(agency.agency_code, 0)
            agency_code_suffix += 1
            self.agency_code_suffix[agency.agency_code] = agency_code_suffix
            agency.agency_id = f'{agency.agency_code}_{agency_code_suffix}'


    def parse_bfkoord_geo(self):
        for line in open(self.get_path(self.get_name('BFKOORD_GEO')),
                         encoding='iso-8859-1'):
            stop = {
              'stop_id': int(line[:8]),
              'stop_lon': line[8:17].strip(),
              'stop_lat': line[19:28].strip(),
              'stop_name': line[39:].strip()
            }
            self.write_stop(stop)

    def parse_bitfield(self):
        self.services = {}
        self.bitfields = {}
        for line in open(self.get_path(self.get_name('BITFELD'))):
            service_id = line[:6]
            # "For technical reasons 2 bits are inserted directly
            # before the first day of the start of the timetable period
            # and two bits directly after the last day at the end of the
            # timetable period."
            bits = Bits(hex=line[6:])[2:]
            self.services[service_id] = bits
            self.bitfields[bits] = service_id
        #  add dummy bitfield for all days
        service_id = '000000'
        bits_ones = ~Bits(length=bits.length)
        self.services[service_id] = bits_ones
        self.bitfields[bits_ones] = service_id


    def parse_infotext(self):
        infotext = {}
        for line in open(self.get_path(self.get_name('INFOTEXT_DE')),
                         encoding='iso-8859-1'):
            infotext[line[0:7]] = line[8:].strip()

        return infotext

    def parse_fplan(self):
        state = 'meta'
        self.meta = {}
        self.stop_informations = []
        linenumber = 0
        self.trip_id = 0
        self.hafas_trip_id = 0
        self.route_id = 0
        service_id = 0
        for line in open(self.get_path(self.get_name('FPLAN')),
                         encoding='latin1'):
            linenumber += 1
            if line.startswith('%'):
                continue
            if line.startswith('*'):
                if line.startswith('*Z'):
                    #  new trip starts
                    #  write data for previous trips
                    self.write_trips()
                    #  reset data
                    self.meta = {}
                    self.stop_informations = []
                state = 'meta'
                self.meta.update(self.parse_fplan_meta(line))

            else:
                if not state == 'data':
                    #  beginning of data block


                    state = 'data'
                    stop_sequence = 0
                    self.write_route(self.meta)
                stop_sequence += 1
                stop_line_info = self.parse_schedule(line)
                self.stop_informations.append(stop_line_info)
                self.meta['headsign'] = stop_line_info['stop_name']

        #  Finally write last trips
        self.write_trips()


    def write_trips(self):
        service_trips = self.meta.get('service_trips', list())
        n_service_trips = len(service_trips)
        if n_service_trips > 1:
            for i in range(n_service_trips-1):
                self.combine_verkehrstage(i, service_trips, n_service_trips)

        for i, service_trip in enumerate(service_trips):
            #if len(service_trips) > 1:
                ##print(self.hafas_trip_id, service_trip.begin, service_trip.begin_time, service_trip.end, service_trip.end_time)
                #if i > 0 and service_trip.begin != service_trips[i-1].end:
                    #raise
                #if i +1 < len(service_trips) and service_trip.end != service_trips[i+1].begin:
                    #raise

            service_id = service_trip.no or "000000"
            bits = self.services[service_id]
            if not bits:
                continue
            self.write_trip(service_id,
                            self.meta)
            trips_started = False
            for stop_sequence, stop_line in enumerate(self.stop_informations):
                stop_id = stop_line['stop_id']
                if not trips_started and not stop_id == service_trip.begin:
                    # if a stop occures more than once in a route,
                    # the departure_time for the starting stop is defined
                    # otherwise, service_trip.begin_time is None
                    if ((not service_trip.begin_time) or
                        (service_trip.begin_time == stop_line.get('departure_time'))):
                        continue
                trips_started = True
                self.write_stop_time(stop_sequence + 1,
                                     stop_line)
                if stop_id == service_trip.end:
                    # if a stop occures more than once in a route,
                    # the arrival_time for the final stop is defined
                    # otherwise, service_trip.end_time is None
                    if ((not service_trip.end_time) or
                        (service_trip.end_time == stop_line.get('arrival_time'))):
                        break
            self.trip_id += 1
        self.hafas_trip_id += 1

    def combine_verkehrstage(self, i, service_trips, n_service_trips):
        #print(self.trip_id, i)
        begin_service_trip = service_trips[i]
        j = i + 1
        end_service_trip = service_trips[j]
        self.combine_verkehrstage_inner(j,
                                        service_trips,
                                        begin_service_trip,
                                        end_service_trip,
                                        n_service_trips)

    def combine_verkehrstage_inner(self,
                                   j,
                                   service_trips,
                                   begin_service_trip,
                                   end_service_trip,
                                   n_service_trips):
        begin = begin_service_trip.begin
        begin_time = begin_service_trip.begin_time
        bits1 = self.services[begin_service_trip.no]

        end = end_service_trip.end
        end_time = end_service_trip.end_time
        bits2 = self.services[end_service_trip.no]
        #  bitvise operations
        common_days = bits1 & bits2
        only_1 = ~bits2 & bits1
        only_2 = ~bits1 & bits2
        #  get the according service_ids
        service_id_1 = self.get_new_service_id(only_1)
        service_id_2 = self.get_new_service_id(only_2)
        begin_service_trip.no = service_id_1
        end_service_trip.no = service_id_2
        #  create a new trip for the common days
        service_id_common = self.get_new_service_id(common_days)
        #print(service_id_1, service_id_2, service_id_common)
        common_service_trip = ServiceTrip(no=service_id_common,
                                          begin=begin,
                                          end=end,
                                          begin_time=begin_time,
                                          end_time=end_time)
        service_trips.append(common_service_trip)

        if j + 1 < n_service_trips:
            j += 1
            end_service_trip = service_trips[j]
            self.combine_verkehrstage_inner(j,
                                            service_trips,
                                           common_service_trip,
                                           end_service_trip,
                                           n_service_trips)

    def get_new_service_id(self, bits):
        service_id = self.bitfields.get(bits)
        if not service_id:
            service_id = f'{self.service_id_new:05}'
            self.services[service_id] = bits
            self.bitfields[bits] = service_id
            self.service_id_new -= 1
        return service_id


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
            'trainnumber' : line[3:8].strip(),
            #'line_number': line[3:8] + "." + line[9:15],
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
        service_trips = self.meta.get('service_trips', list())
        meta_type = line[3:5]
        if meta_type == 'VE':
            begin = int(line[6:14].strip())
            end = int(line[14:22].strip())
            service_id = line[22:28].strip()
            service_trip = ServiceTrip(service_id, begin, end)
            if len(line) >= 30:
                service_trip.begin_time = self.parse_time(line[31:35])
                service_trip.end_time = self.parse_time(line[38:42])
            service_trips.append(service_trip)
        return {
            'service_trips': service_trips,
        }

    def parse_fplan_meta_I(self, line):
        code = line[3:5]
        nr = line[29:36]
        text = self.infotext[nr].strip()
        if code == "ZN" or code == "RN":
            return {'info_text' : text}
        return {}

    def parse_fplan_meta_L(self, line):
        return {
          'trip_no' : line[3:12].strip()
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
