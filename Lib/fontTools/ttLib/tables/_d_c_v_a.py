from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.fixedTools import (
    fixedToFloat as fi2fl,
    floatToFixed as fl2fi,
    floatToFixedToStr as fl2str,
    strToFixedToFloat as str2fl,
    floatToFixedToFloat as fl2fifl
)
from fontTools.ttLib import TTLibError
from . import DefaultTable
import struct


DCVA_AXIS_FORMAT = """
    > # big endian
    more:?
    axisNameID:H
    minValue:f
    maxValue:f
"""

class table__d_c_v_a(DefaultTable.DefaultTable):
    dependencies = ["glyf"]

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)

    def compile(self, ttFont):
        data = b""
        more = True
        for i, glyphAxisCollection in enumerate(self.glyphAxisCollections):
            if len(self.glyphAxisCollections) - i == 1:
                more = False
            data = data + glyphAxisCollection.compile(more)
        return data

    def decompile(self, data, ttFont):
        self.glyphAxisCollections = []
        moreCollection = True
        while moreCollection:
            glyphAxisCollection = GlyphAxisCollection()
            data, moreCollection, glyphID, axes = glyphAxisCollection.decompile(data)
            glyphAxisCollection.glyphID = glyphID
            glyphAxisCollection.axes = axes
            self.glyphAxisCollections.append(glyphAxisCollection)

    def toXML(self, writer, ttFont):
        writer.begintag("glyphVariationAxis")
        writer.newline()
        for glyphAxisCollection in self.glyphAxisCollections:
            glyphAxisCollection.toXML(writer, ttFont)
            writer.newline()
        writer.endtag("glyphVariationAxis")

    def fromXML(self, name, attrs, content, ttFont):
        self.glyphAxisCollections = []
        for element in content:
            if not isinstance(element, tuple):
                continue
            name, attrs, contentAxes = element
            glyphAxisCollection = GlyphAxisCollection()
            glyphAxisCollection.fromXML(name, attrs, contentAxes, ttFont)
            self.glyphAxisCollections.append(glyphAxisCollection)

class GlyphAxisCollection(object):
    def __init__(self):
        self.more = True

    def compile(self, more):
        data = b""
        self.more = struct.pack(">?", more)
        data = self.more + struct.pack(">H", self.glyphID)
        moreAxis = True
        for i, axis in enumerate(self.axes):
            if len(self.axes) - i == 1:
                moreAxis = False
            axisData = axis.compile(moreAxis)
            data += axisData
        return data

    def decompile(self, data):
        moreCollection = struct.unpack(">?", data[:1])[0]
        data = data[1:]
        self.glyphID = struct.unpack(">H", data[:2])[0]
        data = data[2:]

        self.axes = []
        moreAxis = True
        while moreAxis:
            axis = Axis()
            data, moreAxis, axisNameID, minValue, maxValue = axis.decompile(data)
            axis.axisNameID = axisNameID
            axis.minValue = minValue
            axis.maxValue = maxValue
            self.axes.append(axis)
        return data, moreCollection, self.glyphID, self.axes

    def toXML(self, writer, ttFont):
        glyphOrder = ttFont.getGlyphOrder()
        name = "glyph"
        attrs =  str(glyphOrder[self.glyphID])
        writer.begintag("axes", glyph=attrs)
        writer.newline()
        for axis in self.axes:
            axis.toXML(writer, ttFont)
            writer.newline()
        writer.endtag("axes")

    def fromXML(self, name, attrs, content, ttFont):
        self.glyphID = int(ttFont.getGlyphID(attrs["glyph"]))
        self.axes = []
        for element in content:
            if not isinstance(element, tuple):
                continue
            name, attrs, content = element
            axis = Axis()
            axis.fromXML(name, attrs, content, ttFont)
            self.axes.append(axis)

class Axis(object):
    def compile(self, more):
        moreAxis = struct.pack(">?", more)
        axisNameID = struct.pack(">H", self.axisNameID)
        minValue = struct.pack(">f", fl2fifl(self.minValue,14))
        maxValue = struct.pack(">f", fl2fifl(self.maxValue,14))
        return moreAxis + axisNameID + minValue + maxValue

    def decompile(self, data):
        more = struct.unpack(">?", data[:1])[0]
        data = data[1:]
        self.axisNameID = struct.unpack(">H", data[:2])[0]
        data = data[2:]
        minValue = struct.unpack(">f", data[:4])[0]
        self.minValue = fl2fifl(minValue,14)
        data = data[4:]
        maxValue = struct.unpack(">f", data[:4])[0]
        self.maxValue = fl2fifl(maxValue,14)
        data = data[4:]
        return data, more, self.axisNameID, self.minValue, self.maxValue

    def toXML(self, writer, ttFont):
        nameID = ("nameID", self.axisNameID)
        minValue = ("minValue", fl2str(self.minValue, 16))
        maxValue = ("maxValue", fl2str(self.maxValue, 16))
        attrs = (nameID,  minValue, maxValue)
        writer.simpletag("axis", attrs)

    def fromXML(self, name, attrs, _content, ttFont):
        assert(name == "axis")
        if not isinstance(attrs, tuple):
            pass
        self.axisNameID = int(attrs["nameID"])
        self.minValue = fl2fifl(float(attrs['minValue']), 14)
        self.maxValue = fl2fifl(float(attrs['maxValue']), 14)
