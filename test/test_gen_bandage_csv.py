import falcon_kit.mains.gen_bandage_csv as mod
import helpers
import pytest
import os

def test_help():
    try:
        mod.main(['prog', '--help'])
    except SystemExit:
        pass

def test_main_1(tmpdir, capsys):

    gfa_graph = mod.GFAGraph()
    gfa_graph.add_node('node1', 7, 'ACTGAAA', tags={}, labels={})
    gfa_graph.add_node('node2', 10, 'AAACCCGGGT', tags={}, labels={})
    gfa_graph.add_node('node3', 7, 'ACTGAAA', tags={}, labels={})
    gfa_graph.add_node('node4', 10, 'AAACCCGGGT', tags={}, labels={})
    gfa_graph.add_node('node5', 7, 'ACTGAAA', tags={}, labels={})
    gfa_graph.add_node('node6', 10, 'AAACCCGGGT', tags={}, labels={})
    gfa_graph.add_node('node7', 14, 'AACCCGGGTACTGG', tags={}, labels={})
    gfa_graph.add_edge('edge1', 'node1', '+', 'node2', '+', 4, 7, 0, 3, '*', tags={}, labels={})
    gfa_graph.add_edge('edge2', 'node3', '+', 'node4', '+', 4, 7, 0, 3, '*', tags={}, labels={})
    gfa_graph.add_edge('edge3', 'node5', '+', 'node6', '+', 4, 7, 0, 3, '*', tags={}, labels={})
    gfa_graph.add_edge('edge4', 'node6', '+', 'node7', '+', 1, 10, 0, 9, '*', tags={}, labels={})
    gfa_graph.add_path('000000F', ['node1', 'node2'], ['3M', '7M'], tags={}, labels={})
    gfa_graph.add_path('000001F', ['node3', 'node4'], ['3M', '7M'], tags={}, labels={})
    gfa_graph.add_path('000002F', ['node5', 'node6'], ['3M', '7M'], tags={}, labels={})
    # Node 6 is shared between two contigs. It's color should be yellow, and the contig list should contain both contigs.
    gfa_graph.add_path('000003F', ['node6', 'node7'], ['9M', '5M'], tags={}, labels={})

    gfa_json_file = tmpdir.join('graph.gfa.json')
    gfa_json_file.write(mod.serialize_gfa(gfa_graph))

    argv = ['prog',
            str(gfa_json_file),
            ]
    mod.main(argv)
    out, err = capsys.readouterr()
    result = out

    expected = """\
Node name,Contig,Color,OrdinalID
node1,000000F,#1CE6FF,0
node2,000000F,#1CE6FF,1
node3,000001F,#FF34FF,0
node4,000001F,#FF34FF,1
node5,000002F,#FF4A46,0
node6,000002F;000003F,#FFFF00,0
node7,000003F,#008941,1
"""

    assert(result == expected)
