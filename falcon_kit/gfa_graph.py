
import os
import sys
import json
import collections

GFA_H_TAG = 'H'
GFA_S_TAG = 'S'
GFA_L_TAG = 'L'
GFA_P_TAG = 'P'
GFA_ORIENT_FWD = '+'
GFA_ORIENT_REV = '-'
GFA_SEQ_UNKNOWN = '*'
GFA_LINK_CIGAR_UNKNOWN = '*'
GFA2_E_TAG = 'E'

KW_NAME = 'name'
KW_TAGS = 'tags'
KW_LABELS = 'labels'

KW_NODE_SEQ = 'seq'
KW_NODE_LEN = 'len'

KW_EDGE_SOURCE = 'v'
KW_EDGE_SOURCE_ORIENT = 'v_orient'
KW_EDGE_SINK = 'w'
KW_EDGE_SINK_ORIENT = 'w_orient'
KW_EDGE_CIGAR = 'cigar'
KW_EDGE_SOURCE_START = 'v_start'
KW_EDGE_SOURCE_END = 'v_end'
KW_EDGE_SINK_START = 'w_start'
KW_EDGE_SINK_END = 'w_end'

KW_PATH_NODES = 'nodes'
KW_PATH_CIGARS = 'cigars'

"""
GFA-1:
- H line: line = '\t'.join([GFA_H_TAG, '\tVN:Z:1.0'])
- S line: line = '\t'.join([GFA_S_TAG, rname, GFA_SEQ_UNKNOWN if (not write_reads) else r.sequence, 'LN:i:%s' % len(r.sequence)])
- L line: line = '\t'.join([GFA_L_TAG, edge.sg_edge.v_name, edge.sg_edge.v_orient, edge.sg_edge.w_name, edge.sg_edge.w_orient, cig_str])
- P line: line = '\t'.join([GFA_P_TAG, ctg_name, ','.join(segs), ','.join(segs_cigar)]

GFA-2:
- H line: line = '\t'.join([GFA_H_TAG, '\tVN:Z:2.0'])
- S line: line = '\t'.join([GFA_S_TAG, rname, str(len(r.sequence)), GFA_SEQ_UNKNOWN if (not write_reads) else r.sequence])
- E line: line = '\t'.join([GFA2_E_TAG, edge_name, source_node, sink_node, source_start, source_end, sink_start, sink_end, cig_str])

"""

# The yellow color will be used for nodes which belong to multiple contigs.
color_yellow = "#FFFF00"
# General color list.
colors = [
        "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059",
        "#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#8FB0FF", # "#997D87",
        "#809693", "#FEFFE6", "#4FC601", "#3B5DFF", "#FF2F80",
        "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
        "#DDEFFF", "#7B4F4B", "#A1C299", "#0AA6D8", "#00846F",
        "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99",
        "#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
        "#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",

        "#34362D", "#B4A8BD", "#00A6AA", "#636375", "#A3C8C9", "#FF913F", "#938A81",
        "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
        "#7900D7", "#A77500", "#6367A9", "#A05837", "#772600", "#D790FF", "#9B9700",
        "#549E79", "#FFF69F", "#72418F", "#BC23FF", "#99ADC0", "#922329",
        "#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
        "#83AB58", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66",
        "#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#5B4E51",
        "#C895C5", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379",

        "#7A7BFF", "#D68E01", "#78AFA1", "#FEB2C6", "#75797C", "#837393", "#943A4D",
        "#B5F4FF", "#D2DCD5", "#9556BD", "#6A714A", "#02525F", "#0AA3F7", "#E98176",
        "#DBD5DD", "#5EBCD1", "#3D4F44", "#7E6405", "#02684E", "#962B75", "#8D8546", "#9695C5",
        "#E773CE", "#D86A78", "#3E89BE", "#CA834E", "#518A87", "#5B113C", "#55813B", "#E704C4",
        "#A97399", "#4B8160", "#59738A", "#FF5DA7", "#F7C9BF", "#643127", "#513A01",
        "#6B94AA", "#51A058", "#A45B02", "#E20027", "#E7AB63", "#4C6001", "#9C6966",
        "#64547B", "#97979E", "#006A66", "#F4D749", "#0045D2", "#006C31", "#DDB6D0",
        "#7C6571", "#9FB2A4", "#00D891", "#15A08A", "#BC65E9", "#FFFFFE", "#C6DC99",

        "#671190", "#6B3A64", "#F5E1FF", "#FFA0F2", "#CCAA35", "#8BB400", "#797868",
        "#C6005A", "#C86240", "#29607C", "#7D5A44", "#CCB87C", "#B88183",
        "#AA5199", "#B5D6C3", "#A38469", "#9F94F0", "#A74571", "#B894A6", "#71BB8C", "#00B433",
        "#789EC9", "#6D80BA", "#953F00", "#5EFF03", "#E4FFFC", "#1BE177", "#BCB1E5", "#76912F",
        "#0060CD", "#D20096", "#895563", "#5B3213", "#A76F42", "#89412E",
        "#494B5A", "#A88C85", "#F4ABAA", "#A3F3AB", "#00C6C8", "#EA8B66", "#958A9F",
        "#BDC9D2", "#9FA064", "#BE4700", "#658188", "#83A485", "#47675D", "#3A3F00",
        "#DFFB71", "#868E7E", "#98D058", "#6C8F7D", "#D7BFC2", "#D83D66",

        "#2F5D9B", "#6C5E46", "#D25B88", "#5B656C", "#00B57F", "#545C46", "#866097", "#365D25",
        "#252F99", "#00CCFF", "#674E60", "#FC009C", "#92896B"
]

class GFAGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.paths = {}

        """
        Node: {KW_NAME: '01234', KW_NODE_SEQ: 'ACTG', 'len': 4}
        Node: {'name': '56789', KW_NODE_SEQ: 'CAGT', 'len': 4}
        Edge: {KW_NAME: 'edge1', 'source': '01234', 'sink': '56789', 'cigar': '*', 'source_start': 3, 'source_end': 4, 'sink_start': 0, 'sink_end': 1}
        Path: {KW_NAME: '000000F', 'nodes': ['01234', '56789'], '
        """

    def add_node(self, node_name, node_len, node_seq='*', tags={}, labels={}):
        if len(node_name) == 0:
            raise 'Node name should be a non-empty string.\n'
        if node_len < 0:
            raise 'Node length should be >= 0.\n'
        if len(node_seq) == 0:
            raise 'Node sequence should be a non-empty string. Use "*" instead.\n'
        if isinstance(tags, dict) == False:
            raise 'The tags object must be a dict.\n'
        if isinstance(labels, dict) == False:
            raise 'The labels object must be a dict.\n'

        self.nodes[node_name] = {
                                    KW_NAME: node_name,
                                    KW_NODE_LEN: node_len,
                                    KW_NODE_SEQ: node_seq,
                                    KW_TAGS: tags,
                                    KW_LABELS: labels
                                }

    def add_edge(self, edge_name, source, source_orient, sink, sink_orient, source_start, source_end, sink_start, sink_end, cigar, tags={}, labels={}):
        """
        source_orient   + if fwd, - otherwise.
        sink_orient   + if fwd, - otherwise.
        """
        if len(edge_name) == 0:
            raise 'Edge name should be a non-empty string.\n'
        if len(source) == 0:
            raise 'Source node not specified.\n'
        if len(sink) == 0:
            raise 'Sink node not specified.\n'
        if source_orient not in '+-':
            raise 'Source orientation should be either "+" or "-".\n'
        if sink_orient not in '+-':
            raise 'Sink orientation should be either "+" or "-".\n'
        if source_start < 0 or source_end < 0:
            raise 'Source coordinates should be >= 0.\n'
        if sink_start < 0 or sink_end < 0:
            raise 'Sink coordinates should be >= 0.\n'
        if len(cigar) == 0:
            raise 'Cigar string should not be empty. Use "*" instead.\n'
        if source_end < source_start:
            sys.stderr.write('ERROR with: source = %s, source_start = %s, source_end = %s, sink = %s, sink_start = %s, sink_end = %s\n' % (source, source_start, source_end, sink, sink_start, sink_end))
            raise 'Source end coordinate should be >= source start coordinate.\n'
        if sink_end < sink_start:
            raise 'Sink end coordinate should be >= sink start coordinate.\n'
        if isinstance(tags, dict) == False:
            raise 'The tags object must be a dict.\n'
        if isinstance(labels, dict) == False:
            raise 'The labels object must be a dict.\n'

        self.edges[str((source, sink))] = {
                                        KW_NAME: edge_name,
                                        KW_EDGE_SOURCE: source,
                                        KW_EDGE_SOURCE_ORIENT: source_orient,
                                        KW_EDGE_SINK: sink,
                                        KW_EDGE_SINK_ORIENT: sink_orient,
                                        KW_EDGE_SOURCE_START: source_start,
                                        KW_EDGE_SOURCE_END: source_end,
                                        KW_EDGE_SINK_START: sink_start,
                                        KW_EDGE_SINK_END: sink_end,
                                        KW_EDGE_CIGAR: cigar,
                                        KW_TAGS: tags,
                                        KW_LABELS: labels
                                    }

    def add_path(self, path_name, path_nodes, path_cigars, tags={}, labels={}):
        """
        path_nodes is a list of nodes which should be joined
        consecutively in a path.
        path_cigars is a list of CIGAR strings describing how the
        two neighboring nodes are joined.
        len(path_nodes) == len(path_cigars)
        """
        if len(path_name) == 0:
            raise 'Path name should be a non-empty string.\n'
        if len(path_nodes) == 0:
            raise 'Path nodes should be a non-empty list.\n'
        if len(path_cigars) == 0:
            raise 'Path cigars should be a non-empty list.\n'
        if isinstance(tags, dict) == False:
            raise 'The tags object must be a dict.\n'
        if isinstance(labels, dict) == False:
            raise 'The labels object must be a dict.\n'
        if len(path_nodes) != len(path_cigars):
            raise 'The path_nodes and path_cigars should have the same length.\n'

        self.paths[path_name] = {
                                    KW_NAME: path_name,
                                    KW_PATH_NODES: path_nodes,
                                    KW_PATH_CIGARS: path_cigars,
                                    KW_TAGS: tags,
                                    KW_LABELS: labels
                                }

    def write_bandage_csv(self, fp_out):
        node_to_contig = collections.defaultdict(list)
        node_to_primary_contig = collections.defaultdict(set)
        node_to_ordinal_id = {}
        node_to_color = {}
        contig_color_dict = {}

        # Iterate through each path (contigs are specified by paths).
        for num_contigs, path_name in enumerate(sorted(self.paths.keys())):
            path_data = self.paths[path_name]

            # Get the primary contig name.
            ctg_name = path_name.split('-')[0].split('_')[0]

            # If the contig name is not yet indexed, set it's new color.
            contig_color_dict[ctg_name] = contig_color_dict.get(ctg_name, colors[len(contig_color_dict.keys()) % len(colors)])

            # For each node in path, label it's contig and mark it's color.
            for i, node_name in enumerate(path_data[KW_PATH_NODES]):
                node_to_contig[node_name].append(path_name)
                node_to_primary_contig[node_name].add(ctg_name)
                node_to_color[node_name] = contig_color_dict[ctg_name]
                node_to_ordinal_id[node_name] = i

        fp_out.write('Node name,Contig,Color,OrdinalID\n')
        for node in sorted(node_to_contig.keys()):
            contigs = node_to_contig[node]
            contig_names = ';'.join(contigs)
            if len(node_to_primary_contig[node]) == 1:
                # If a node belongs to only one contig, color it as such.
                fp_out.write('{},{},{},{}\n'.format(node, contig_names, node_to_color[node], node_to_ordinal_id[node]))
            else:
                # Yellow color for undefined nodes.
                fp_out.write('{},{},{},{}\n'.format(node, contig_names, color_yellow, node_to_ordinal_id[node]))

    def write_gfa_v1(self, fp_out):
        # Header
        line = '\t'.join([GFA_H_TAG, 'VN:Z:1.0'])
        fp_out.write(line + '\n')

        # Sequences.
        for node_name, node_data in self.nodes.items():
            line = '\t'.join([  GFA_S_TAG,
                                node_data[KW_NAME],
                                node_data[KW_NODE_SEQ],
                                'LN:i:%d' % node_data[KW_NODE_LEN]])
            fp_out.write(line + '\n')

        for edge, edge_data in self.edges.items():
            cigar = edge_data[KW_EDGE_CIGAR] if edge_data[KW_EDGE_CIGAR] != '*' else '%dM' % (abs(edge_data[KW_EDGE_SINK_END] - edge_data[KW_EDGE_SINK_START]))

            line = '\t'.join([str(val) for val in
                                [  GFA_L_TAG,
                                    edge_data[KW_EDGE_SOURCE],
                                    edge_data[KW_EDGE_SOURCE_ORIENT],
                                    edge_data[KW_EDGE_SINK],
                                    edge_data[KW_EDGE_SINK_ORIENT],
                                    cigar
                                ]
                            ])
            fp_out.write(line + '\n')

        for path_name, path_data in self.paths.items():
            line = '\t'.join([GFA_P_TAG, path_data[KW_NAME], ','.join(path_data[KW_PATH_NODES]), ','.join(path_data[KW_PATH_CIGARS])])
            fp_out.write(line + '\n')

    def write_gfa_v2(self, fp_out):
        # Header
        line = '\t'.join([GFA_H_TAG, 'VN:Z:2.0'])
        fp_out.write(line + '\n')

        # Sequences.
        for node_name, node_data in self.nodes.items():
            line = '\t'.join([  GFA_S_TAG,
                                node_data[KW_NAME],
                                str(node_data[KW_NODE_LEN]),
                                node_data[KW_NODE_SEQ]])
            fp_out.write(line + '\n')

        for edge, edge_data in self.edges.items():
            v = edge_data[KW_EDGE_SOURCE]
            w = edge_data[KW_EDGE_SINK]
            v_len = self.nodes[v][KW_NODE_LEN]
            w_len = self.nodes[w][KW_NODE_LEN]

            # GFA-2 specifies a special char '$' when a coordinate is the same as the sequence length.
            v_start = str(edge_data[KW_EDGE_SOURCE_START]) + ('$' if edge_data[KW_EDGE_SOURCE_START] == v_len else '')
            v_end = str(edge_data[KW_EDGE_SOURCE_END]) + ('$' if edge_data[KW_EDGE_SOURCE_END] == v_len else '')
            w_start = str(edge_data[KW_EDGE_SINK_START]) + ('$' if edge_data[KW_EDGE_SINK_START] == w_len else '')
            w_end = str(edge_data[KW_EDGE_SINK_END]) + ('$' if edge_data[KW_EDGE_SINK_END] == w_len else '')

            line = '\t'.join([str(val) for val in
                                [  GFA2_E_TAG, edge_data[KW_NAME],
                                    edge_data[KW_EDGE_SOURCE] + edge_data[KW_EDGE_SOURCE_ORIENT],
                                    edge_data[KW_EDGE_SINK] + edge_data[KW_EDGE_SINK_ORIENT],
                                    v_start, v_end,
                                    w_start, w_end,
                                    edge_data[KW_EDGE_CIGAR],
                                ]
                            ])
            fp_out.write(line + '\n')

def serialize_gfa(gfa_graph):
    gfa_dict = {}
    gfa_dict['nodes'] = gfa_graph.nodes
    gfa_dict['edges'] = gfa_graph.edges
    gfa_dict['paths'] = gfa_graph.paths
    return json.dumps(gfa_dict, separators=(', ', ': '), sort_keys=True)

def deserialize_gfa(fp_in):
    gfa_dict = json.load(fp_in)
    gfa = GFAGraph()
    gfa.nodes = gfa_dict['nodes']
    gfa.edges = gfa_dict['edges']
    gfa.paths = gfa_dict['paths']
    return gfa
