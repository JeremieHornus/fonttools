from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.fixedTools import (
    fixedToFloat as fi2fl,
    floatToFixed as fl2fi,
    floatToFixedToStr as fl2str,
    strToFixedToFloat as str2fl,
)
from fontTools.ttLib import TTLibError
from . import DefaultTable
import struct


DCVA_AXIS_FORMAT = """
    > # big endian
    more:           ?
    axisNameID:     H
    minValue:       f
    maxValue:       f
"""

class table__d_c_v_a(DefaultTable.DefaultTable):
    dependencies = ["name"]

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.glyphAxisCollections = []

    def compile(self, ttFont):
        data = b""
        for glyphAxisCollection in self.glyphAxisCollections:
            data = data + glyphAxisCollection.compile()
        return data

    def decompile(self, data, ttFont):
        self.glyphAxisCollections = []
        more = True
        while more:
            glyphAxisCollection = GlyphAxisCollection()
            more, data = glyphAxisCollection.decompile()

    def toXML(self, writer, ttFont):
        for glyphAxisCollection in self.glyphAxisCollections:
            glyphAxisCollection.toXML(writer, ttFont)

    def fromXML(self, name, attrs, content, ttFont):
        for element in content:
            name, attrs, content = element
            glyphAxisCollection = GlyphAxisCollection()
            glyphAxisCollection.fromXML(name, attrs, content, ttFont)
            self.glyphAxisCollections.append(glyphAxisCollection)

class GlyphAxisCollection(object):

    def compile(self):
        data = b""
        data = data + struct.pack(">H", self.glyphID)
        for axis in self.axes:
            data = data + axis.compile()
        return data

    def decompile(self, data):
        moreGlyphAxisCollection = struct.unpack(">?", data[:1])[0]
        data = data[1:]
        self.glyphID = struct.unpack(">H", data[:2])[0]
        data = data[2:]

        self.axes = []
        more = True
        while more:
            axis = Axis()
            more, data = axis.decompile(data)
            self.axes.append(axis)
        return moreGlyphAxisCollection, data

    def toXML(self, writer, ttFont):
        glyphOrder = ttFont.getGlyphOrder()
        attrs = ["glyph", ("glyphID", str(glyphOrder[self.glyphID]))]
        writer.begintag("axes", attrs)
        for axis in axes:
            writer.newline()
            axis.toXML(writer, ttFont)
        writer.newline()
        writer.endtag("axes")

    def fromXML(self, name, attrs, content, ttFont):
        assert(name == "axes")
        self.glyphID = attrs["glyph"]
        self.axes = []
        for element in content:
            if not isinstance(element, tuple):
                continue
            name, attrs, content = element
            axis = Axis()
            axis.fromXML(name, attrs, content, ttFont)
            self.axes.append(axis)

class Axis(object):

    def compile(self):
        return sstruct.pack(DCVA_AXIS_FORMAT, self)

    def decompile(self):
        more = struct.unpack(">?", data[:1])[0]
        data = data[1:]
        self.axisNameID = struct.unpack(">H", data[:2])
        data = data[2:]
        minValue = struct.unpack(">f", data[:4])
        self.minValue = fl2fifl(minValue,14)
        data = data[4:]
        maxValue = struct.unpack(">f", data[:4])
        self.maxValue = fl2fifl(maxValue,14)
        data = data[4:]
        return more, data

    def toXML(self, writer, ttFont):
        nameID = ("name", ttFont["name"].getDebugName(self.axisNameID))
        minValue = ("MinValue", fl2str(self.minValue, 16))
        maxValue = ("MaxValue", fl2str(self.maxValue, 16))
        attrs = [nameID + minValue + maxValue]
        writer.simpletag("axis", attrs)
        writer.newline()

    def fromXML(self, name, attrs, _content, ttFont):
        assert(name == "axis")
        self.axisNameID = attrs["name"]
        self.minValue = attrs['minValue']
        self.maxValue = attrs['maxValue']
