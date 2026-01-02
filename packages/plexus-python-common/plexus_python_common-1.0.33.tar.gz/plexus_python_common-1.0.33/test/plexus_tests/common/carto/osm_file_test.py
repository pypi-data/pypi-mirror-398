import unittest
import unittest.mock

import lxml.etree

from plexus.common.carto import OSMFile
from plexus.common.proj import Coord
from plexus.common.proj import make_proj


class MockedTree(object):
    def __init__(self, xml_literal: str):
        self.root = lxml.etree.fromstring(xml_literal)

    def getroot(self):
        return self.root


class OSMFileTest(unittest.TestCase):

    def test_from_coords_list(self):
        proj = make_proj("eqdc:lat_1=0.0,lat_2=5.0")

        coords_list = [
            [
                Coord.from_latlon(0.0, 0.0, 0.0, proj=proj),
                Coord.from_latlon(0.0, 0.0000001, 1.0, proj=proj),
                Coord.from_latlon(0.0000001, 0.0000001, 0.0, proj=proj),
                Coord.from_latlon(0.0000001, 0.0, -1.0, proj=proj),
            ],
            [
                Coord.from_latlon(0.0000001, 0.0, -1.0, proj=proj),
                Coord.from_latlon(0.0000001, 0.0000001, 0.0, proj=proj),
                Coord.from_latlon(0.0, 0.0000001, 1.0, proj=proj),
                Coord.from_latlon(0.0, 0.0, 0.0, proj=proj),
            ],
        ]

        way_tags_list = [
            {"dummy_key": "dummy_value_x"},
            {"dummy_key": "dummy_value_y"},
        ]

        osm = OSMFile.from_coords_list(coords_list, way_tags_list)

        self.assertEqual(len(osm.nodes), 8)
        self.assertEqual(len(osm.ways), 2)

    def test_load_file(self):
        proj = make_proj("eqdc:lat_1=0.0,lat_2=5.0")

        with unittest.mock.patch("lxml.etree.parse") as mock_parse:
            mock_parse.return_value = MockedTree(
                # language=xml
                """
                <osm version="0.6" generator="Plexus">
                    <node id="1" action="modify" visible="true" version="1" lat="0.0" lon="0.0">
                        <tag k="z" v="0.0"/>
                        <tag k="dummy_key" v="dummy_value_a"/>
                    </node>
                    <node id="2" action="modify" visible="true" version="1" lat="0.0" lon="0.0000001">
                        <tag k="z" v="1.0"/>
                        <tag k="dummy_key" v="dummy_value_b"/>
                    </node>
                    <node id="3" action="modify" visible="true" version="1" lat="0.0000001" lon="0.0000001">
                        <tag k="z" v="0.0"/>
                        <tag k="dummy_key" v="dummy_value_c"/>
                    </node>
                    <node id="4" action="modify" visible="true" version="1" lat="0.0000001" lon="0.0">
                        <tag k="z" v="-1.0"/>
                        <tag k="dummy_key" v="dummy_value_d"/>
                    </node>
                    <way id="1" action="modify" visible="true" version="1">
                        <nd ref="1"/>
                        <nd ref="2"/>
                        <nd ref="3"/>
                        <nd ref="4"/>
                        <tag k="dummy_key" v="dummy_value_x"/>
                    </way>
                    <way id="2" action="modify" visible="true" version="1">
                        <nd ref="4"/>
                        <nd ref="3"/>
                        <nd ref="2"/>
                        <nd ref="1"/>
                        <tag k="dummy_key" v="dummy_value_y"/>
                    </way>
                </osm>
                """
            )

            osm = OSMFile.load_file("dummy/file/path.osm", proj)

            mock_parse.assert_called_with("dummy/file/path.osm")

            self.assertEqual(len(osm.nodes), 4)
            self.assertEqual(len(osm.ways), 2)
