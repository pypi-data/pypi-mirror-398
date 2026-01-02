from iker.common.utils.strutils import repr_data

from plexus.common.carto.OSMTags import OSMTags
from plexus.common.proj import Coord


class OSMNode(object):
    """
    Represents node in OSM
    """

    def __init__(self, node_id: int, coord: Coord, tags: OSMTags):
        """
        Creates an instance from the given node id, coord, and tags

        :param node_id: id
        :param coord: node coordinate
        :param tags: tags
        """
        self.node_id = node_id
        self.coord = coord
        self.tags = tags

    def __str__(self):
        return repr_data(self)
