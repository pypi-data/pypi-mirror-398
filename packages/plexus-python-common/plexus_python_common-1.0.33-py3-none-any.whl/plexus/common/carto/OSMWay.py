from iker.common.utils.strutils import repr_data

from plexus.common.carto.OSMTags import OSMTags


class OSMWay(object):
    """
    Represents way in OSM
    """

    def __init__(self, way_id: int, node_ids: list[int], tags: OSMTags):
        """
        Creates an instance from the given way id, node ids, and tags

        :param way_id: id
        :param node_ids: nodes ids
        :param tags: tags
        """
        self.way_id = way_id
        self.node_ids = node_ids
        self.tags = tags

    def __str__(self):
        return repr_data(self)
