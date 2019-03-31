#!/usr/bin/python3
# SPDX-License-Identifier: MIT

import argparse
import binascii
import colorsys
import os
import subprocess
import sys
import tempfile

import yaml


def id_from_name(port, dir='', index=''):
    return (dir + str(index) + '_' + ''.join([s for s in (port['name'].lower().replace(' ', '_')) if s in
                     'abcdefghijklmnopqrstuvwxyz0123456789_']))


def port_cell(port, rowspan=1):
    return "<td rowspan='{2}' port='{0}'>{1}</td>".format(
        port['id'], port['name'], rowspan)


def port_target(port):
    if 'owner' in port:
        return "{0}:{1}".format(port['owner'], port['id'])
    else:
        return "{0}".format(port['id'])


def listify(obj):
    if isinstance(obj, list):
        return obj
    else:
        return [obj]


def generate_bgcolor(str):
    """Generate an arbitrary background color based on a hash of 'str'."""
    crc = binascii.crc32(str.encode('utf-8')) % (1 << 32)
    # pick out some HSV
    h = (crc & 0xFF) / 255.0
    s = ((crc & 0xFF00) >> 8) / 255.0
    v = ((crc & 0xFF0000) >> 16) / 255.0
    # make sure value is high, saturation is low
    s = (s / 4) + 0.25
    v = (v / 4) + 0.75
    return ('#%02x%02x%02x' % tuple([int(x*255) for x in colorsys.hsv_to_rgb(h, s, v)]))


def write_port_n_0(dot, node):
    for port in node['gozintas']:
        dot.write("\t\t\t<tr>{0}</tr>\n".format(port_cell(port)))


def write_port_0_n(dot, node):
    for port in node['gozoutas']:
        dot.write("\t\t\t<tr>{0}</tr>\n".format(port_cell(port)))


def write_port_n_1(dot, node):
    gozin_count = len(node['gozintas'])
    gozout_count = len(node['gozoutas'])
    gozin_itr = iter(node['gozintas'])
    gozout_itr = iter(node['gozoutas'])

    in_port = gozin_itr.__next__()
    out_port = gozout_itr.__next__()

    # do first one
    dot.write("\t\t\t<tr>{0}{1}</tr>\n".format(
        port_cell(in_port), port_cell(out_port, rowspan=gozin_count)))

    # and the rest
    for i in range(0, gozin_count-1):
        in_port = gozin_itr.__next__()
        dot.write("\t\t\t<tr>{0}</tr>\n".format(
            port_cell(in_port)))


def write_port_1_n(dot, node):
    gozin_count = len(node['gozintas'])
    gozout_count = len(node['gozoutas'])
    gozin_itr = iter(node['gozintas'])
    gozout_itr = iter(node['gozoutas'])

    in_port = gozin_itr.__next__()
    out_port = gozout_itr.__next__()

    # do first one
    dot.write("\t\t\t<tr>{0}{1}</tr>\n".format(
        port_cell(in_port, rowspan=gozout_count), port_cell(out_port)))

    # and the rest
    for i in range(0, gozout_count-1):
        out_port = gozout_itr.__next__()
        dot.write("\t\t\t<tr>{0}</tr>\n".format(
            port_cell(out_port)))


def write_port_m_n(dot, node):
    gozin_count = len(node['gozintas'])
    gozout_count = len(node['gozoutas'])
    paired_count = min(gozin_count, gozout_count)

    gozin_itr = iter(node['gozintas'])
    gozout_itr = iter(node['gozoutas'])

    for i in range(0, paired_count):
        in_port = gozin_itr.__next__()
        out_port = gozout_itr.__next__()
        dot.write("\t\t\t<tr>{0}{1}</tr>\n".format(
            port_cell(in_port),
            port_cell(out_port)))

    # We're through all the left/right pairs.
    gozin_count = gozin_count - paired_count
    gozout_count = gozout_count - paired_count

    if gozin_count == 0 and gozout_count > 0:
        # More gozoutas than gozintas
        out_port = gozout_itr.__next__()            
        dot.write("\t\t\t<tr><td rowspan='{0}'></td>{1}</tr>\n".format(
            gozout_count, port_cell(out_port)))
        for i in range(0, gozout_count-1):
            out_port = gozout_itr.__next__()
            dot.write("\t\t\t<tr>{0}</tr>\n".format(
                port_cell(out_port)))
    elif gozin_count > 0 and gozout_count == 0:
        # More gozintas than gozoutas
        in_port = gozin_itr.__next__()            
        dot.write("\t\t\t<tr>{1}<td rowspan='{0}'></td></tr>\n".format(
            gozin_count, port_cell(in_port)))
        for i in range(0, gozin_count-1):
            in_port = gozin_itr.__next__()
            dot.write("\t\t\t<tr>{0}</tr>\n".format(
                port_cell(in_port)))


def write_ports(dot, node):
    """Output table rows for the gozintas and gozoutas.

    This vectors off into subfunctions for the different cases:
        - n in, 0 out
        - 0 in, n out
            - only a single column of inputs or outputs
        - n in, 1 out
        - 1 in, n out
            - two columns, the single input/output spans all rows
        - m in, n out
            - two columns, a row for each input/output. If m != n,
              then a blank cell is created to rowspan the remainder
    """
    if node['gozintas'] and not node['gozoutas']:
        write_port_n_0(dot, node)
    elif not node['gozintas'] and node['gozoutas']:
        write_port_0_n(dot, node)
    elif node['gozintas'] and len(node['gozoutas']) == 1:
        write_port_n_1(dot, node)
    elif len(node['gozintas']) == 1 and node['gozoutas']:
        write_port_1_n(dot, node)
    else:
        write_port_m_n(dot, node)


def main(**kwargs):
    with open(kwargs['input'], 'r') as yaml_file:
        y = yaml.safe_load(yaml_file)

    yaml_directory = os.path.dirname(os.path.abspath(kwargs['input']))

    dot = tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=True)

    # Add defaults as necessary
    for node_id, node in y.items():
        node['id'] = node_id
        if not 'gozintas' in node:
            node['gozintas'] = []
        if not 'gozoutas' in node:
            node['gozoutas'] = []
        for index, port in enumerate(node['gozintas']):
            port['id'] = id_from_name(port, 'in', index)
            port['owner'] = node_id
        for index, port in enumerate(node['gozoutas']):
            port['id'] = id_from_name(port, 'out', index)
            port['owner'] = node_id

    dot.write("digraph G {\n")
    dot.write("\tgraph [fontname = \"helvetica\"; fontsize = 10;];\n")
    dot.write("\tnode [fontname = \"helvetica\"; fontsize = 10;];\n")
    dot.write("\tedge [fontname = \"helvetica\"; fontsize = 10;];\n")
    dot.write("\trankdir = LR;\n")

    # output nodes
    for node_id, node in y.items():
        image = node.get('image', None)

        # relative paths in the YAML should be relative to the YAML file's
        # location, not to the current working directory.
        if image:
            if not os.path.isabs(image):
                image = os.path.join(yaml_directory, image)

        name = node.get('name', node_id)
        bgcolor = node.get('bgcolor', generate_bgcolor(name))

        dot.write("\t{0} [\n".format(node_id))
        dot.write("\t\tshape=plaintext\n")
        dot.write("\t\tlabel=<\n")
        dot.write("\t\t\t<table border='0' cellborder='1' cellspacing='0'>\n")

        colspan = 1
        if node['gozintas'] and node['gozoutas']:
            colspan = 2
        if image:
            dot.write("\t\t\t<tr><td colspan='{0}'><img src='{1}' /></td></tr>\n".format(colspan, image));
        dot.write("\t\t\t<tr><td colspan='{0}' bgcolor='{1}'>{2}</td></tr>\n".format(colspan, bgcolor, name));

        write_ports(dot, node)

        dot.write("\t\t\t</table>\n")
        dot.write("\t\t>];\n\n")

    dot.write("\n")

    for node_id, node in y.items():
        # output linkages between consoles
        if 'gozta' in node:
            for in_port in listify(node['gozta']):
                dot.write("\t{0} -> {1};\n".format(
                    port_target(node), port_target(in_port)))

        # output linkages between ports
        for out_port in node['gozoutas']:
            if 'gozta' in out_port:
                for in_port in listify(out_port['gozta']):
                    dot.write("\t{0} -> {1};\n".format(
                        port_target(out_port), port_target(in_port)))

    dot.write("}\n")
    dot.flush()

    return subprocess.call(["/usr/bin/dot", "-Tpng", "-o" + kwargs['output'], dot.name])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a graph from gozintas to gozoutas.')
    parser.add_argument('input', type=str, help='Graph description input (yaml)')
    parser.add_argument('output', type=str, help='Output image filename')

    args = parser.parse_args()
    sys.exit(main(**vars(args)))
