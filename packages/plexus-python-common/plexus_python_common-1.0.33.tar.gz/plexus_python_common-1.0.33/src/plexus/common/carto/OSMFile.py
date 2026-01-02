from typing import Any, Self

import lxml.etree

from plexus.common.carto.OSMNode import OSMNode
from plexus.common.carto.OSMTags import OSMTags
from plexus.common.carto.OSMWay import OSMWay
from plexus.common.proj import Coord, Proj


class OSMFile(object):
    @classmethod
    def load_file(cls, path: str, proj: Proj | None) -> Self:
        """
        Loads OSM from file given the path

        :param path: path of OSM file
        :param proj: cartographic projection

        :return: an OSM file instance
        """
        root = lxml.etree.parse(path).getroot()

        nodes = {}
        ways = {}
        for elem in root:
            if elem.attrib.get("action") == "delete":
                continue

            if elem.tag == "node":
                # Parse an OSM node
                node_id = int(elem.attrib["id"])
                tags = {}
                for child in elem:
                    if child.tag == "tag":
                        k = child.attrib["k"]
                        v = child.attrib["v"]
                        tags[k] = v

                tags = OSMTags.from_any_tags(tags)
                coord = Coord.from_latlon(
                    float(elem.attrib["lat"]),
                    float(elem.attrib["lon"]),
                    tags.getfloat("z", 0.0),
                    proj,
                )

                nodes[node_id] = OSMNode(node_id, coord, tags)

            elif elem.tag == "way":
                # Parse an OSM way
                way_id = int(elem.attrib["id"])

                tags = {}
                node_ids = []
                for child in elem:
                    if child.tag == "tag":
                        k = child.attrib["k"]
                        v = child.attrib["v"]
                        tags[k] = v
                    elif child.tag == "nd":
                        node_id = int(child.attrib.get("ref"))
                        node_ids.append(node_id)

                tags = OSMTags.from_any_tags(tags)

                ways[way_id] = OSMWay(way_id, node_ids, tags)

        return OSMFile(nodes, ways)

    @classmethod
    def from_coords(cls, coords: list[Coord], way_tags: dict[str, Any] = None) -> Self:
        """
        Constructs a single-way OSM file from the given coords

        :param coords: coords on a single way
        :param way_tags: tags of the corresponding way

        :return: OSM file contains one way
        """
        osm = OSMFile()
        osm.add_way_from_coords(coords, way_tags or {})

        return osm

    @classmethod
    def from_coords_list(cls, coords_list: list[list[Coord]], way_tags_list: list[dict[str, Any]] = None) -> Self:
        """
        Constructs a multi-way OSM file from the given coords

        :param coords_list: coords of each way
        :param way_tags_list: tags of each corresponding way

        :return: OSM file contains multiple ways
        """
        osm = OSMFile()

        if not way_tags_list or len(way_tags_list) != len(coords_list):
            for coords in coords_list:
                osm.add_way_from_coords(coords)
        else:
            for coords, way_tags in zip(coords_list, way_tags_list):
                osm.add_way_from_coords(coords, way_tags or {})

        return osm

    def __init__(self, nodes: dict[int, OSMNode] = None, ways: dict[int, OSMWay] = None):
        """
        Represents an editable general purpose OSM file

        :param nodes: nodes
        :param ways: ways
        """
        self.nodes: dict[int, OSMNode] = {}
        self.ways: dict[int, OSMWay] = {}

        self.next_node_id = 1
        self.next_way_id = 1

        if nodes:
            self.nodes = nodes
            self.next_node_id = max(nodes.keys()) + 1
        if ways:
            self.ways = ways
            self.next_way_id = max(ways.keys()) + 1

    def add_node(self, node: OSMNode) -> OSMNode:
        """
        Adds the given node

        :param node: the node to be added

        :return: added node
        """
        self.nodes[node.node_id] = node
        if node.node_id >= self.next_node_id:
            self.next_node_id = node.node_id + 1
        return node

    def add_node_from_coord(self, coord: Coord, tags: dict[str, Any] = None) -> OSMNode:
        """
        Adds node given the coord and tags

        :param coord: coord of the node
        :param tags: tags of the node

        :return: added node
        """
        return self.add_node(OSMNode(self.next_node_id, coord, OSMTags.from_any_tags(tags)))

    def add_way(self, way: OSMWay) -> OSMWay:
        """
        Adds the given way

        :param way: the way to be added

        :return: added way
        """
        self.ways[way.way_id] = way
        if way.way_id >= self.next_way_id:
            self.next_way_id = way.way_id + 1
        return way

    def add_way_from_coords(self, coords: list[Coord], tags: dict[str, Any] = None) -> OSMWay:
        """
        Adds way given the coords of the nodes and tags

        :param coords: coords of the nodes on the way
        :param tags: tags of the way

        :return: added way
        """
        return self.add_way_from_nodes(coords, tags)

    def add_way_from_node_ids(self, node_ids: list[int], tags: dict[str, Any] = None) -> OSMWay:
        """
        Adds way given the ids of the nodes and tags

        :param node_ids: ids of the nodes on the way
        :param tags: tags of the way

        :return: added way
        """
        return self.add_way_from_nodes(node_ids, tags)

    def add_way_from_nodes(self, elements: list[OSMNode | Coord | int], tags: dict[str, Any] = None) -> OSMWay:
        """
        Adds way given list of the nodes, the coords, or the ids of the nodes and tags

        :param elements: a list of the nodes, the coords, or the ids of the nodes on the way
        :param tags: tags of the way

        :return: added way
        """
        node_ids = []
        for elem in elements:
            if isinstance(elem, OSMNode):
                node_ids.append(self.add_node_from_coord(elem.coord, elem.tags.tags).node_id)
            elif isinstance(elem, Coord):
                node_ids.append(self.add_node_from_coord(elem, {}).node_id)
            else:
                node_ids.append(elem)
        return self.add_way(OSMWay(self.next_way_id, node_ids, OSMTags.from_any_tags(tags)))

    def write(self, filename: str):
        """
        Writes this OSM file instance to the given file name

        :param filename: file path to write into
        """
        root = lxml.etree.Element("osm")
        root.attrib.update({
            "version": "0.6",
            "generator": "Plexus",
        })

        for _, node in self.nodes.items():
            node_elem = lxml.etree.Element("node")
            node_elem.attrib.update(
                {
                    "id": str(node.node_id),
                    "lat": str(node.coord.lat),
                    "lon": str(node.coord.lon),
                    "version": "1",
                }
            )

            for k, v in node.tags.items():
                tag_elem = lxml.etree.Element("tag")
                tag_elem.attrib.update({"k": str(k), "v": str(v)})
                node_elem.append(tag_elem)

            root.append(node_elem)

        for _, way in self.ways.items():
            way_elem = lxml.etree.Element("way")
            way_elem.attrib.update(
                {
                    "id": str(way.way_id),
                    "version": "1",
                }
            )

            for k, v in way.tags.items():
                tag_elem = lxml.etree.Element("tag")
                tag_elem.attrib.update({"k": str(k), "v": str(v)})
                way_elem.append(tag_elem)

            for node_id in way.node_ids:
                nd_elem = lxml.etree.Element("nd")
                nd_elem.attrib.update({"ref": str(node_id)})
                way_elem.append(nd_elem)

            root.append(way_elem)

        s = lxml.etree.tostring(root, pretty_print=True, encoding="unicode")

        with open(filename, "w") as fh:
            fh.write(s)
