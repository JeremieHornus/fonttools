"""Pen recording operations that can be accessed or replayed."""
from fontTools.misc.py23 import *
from fontTools.pens.basePen import AbstractPen, DecomposingPen
from fontTools.pens.pointPen import AbstractPointPen


__all__ = [
    "replayRecording",
    "RecordingPen",
    "DecomposingRecordingPen",
    "RecordingPointPen",
]


def replayRecording(recording, pen):
    """Replay a recording, as produced by RecordingPen or DecomposingRecordingPen,
    to a pen.

    Note that recording does not have to be produced by those pens.
    It can be any iterable of tuples of method name and tuple-of-arguments.
    Likewise, pen can be any objects receiving those method calls.
    """
    for operator,operands in recording:
        getattr(pen, operator)(*operands)


class RecordingPen(AbstractPen):
    """Pen recording operations that can be accessed or replayed.

    The recording can be accessed as pen.value; or replayed using
    pen.replay(otherPen).

    Usage example:
    ==============
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import RecordingPen

    glyph_name = 'dollar'
    font_path = 'MyFont.otf'

    font = TTFont(font_path)
    glyphset = font.getGlyphSet()
    glyph = glyphset[glyph_name]

    pen = RecordingPen()
    glyph.draw(pen)
    print(pen.value)
    """

    def __init__(self):
        self.value = []
    def moveTo(self, p0):
        self.value.append(('moveTo', (p0,)))
    def lineTo(self, p1):
        self.value.append(('lineTo', (p1,)))
    def qCurveTo(self, *points):
        self.value.append(('qCurveTo', points))
    def curveTo(self, *points):
        self.value.append(('curveTo', points))
    def closePath(self):
        self.value.append(('closePath', ()))
    def endPath(self):
        self.value.append(('endPath', ()))
    def addComponent(self, glyphName, transformation):
        self.value.append(('addComponent', (glyphName, transformation)))
    def replay(self, pen):
        replayRecording(self.value, pen)


class DecomposingRecordingPen(DecomposingPen, RecordingPen):
    """ Same as RecordingPen, except that it doesn't keep components
    as references, but draws them decomposed as regular contours.

    The constructor takes a single 'glyphSet' positional argument,
    a dictionary of glyph objects (i.e. with a 'draw' method) keyed
    by thir name.

    >>> class SimpleGlyph(object):
    ...     def draw(self, pen):
    ...         pen.moveTo((0, 0))
    ...         pen.curveTo((1, 1), (2, 2), (3, 3))
    ...         pen.closePath()
    >>> class CompositeGlyph(object):
    ...     def draw(self, pen):
    ...         pen.addComponent('a', (1, 0, 0, 1, -1, 1))
    >>> glyphSet = {'a': SimpleGlyph(), 'b': CompositeGlyph()}
    >>> for name, glyph in sorted(glyphSet.items()):
    ...     pen = DecomposingRecordingPen(glyphSet)
    ...     glyph.draw(pen)
    ...     print("{}: {}".format(name, pen.value))
    a: [('moveTo', ((0, 0),)), ('curveTo', ((1, 1), (2, 2), (3, 3))), ('closePath', ())]
    b: [('moveTo', ((-1, 1),)), ('curveTo', ((0, 2), (1, 3), (2, 4))), ('closePath', ())]
    """
    # raises KeyError if base glyph is not found in glyphSet
    skipMissingComponents = False


class RecordingPointPen(AbstractPointPen):
    """PointPen recording operations that can be accessed or replayed.

    The recording can be accessed as pen.value; or replayed using
    pointPen.replay(otherPointPen).

    Usage example:
    ==============
    from defcon import Font
    from fontTools.pens.recordingPen import RecordingPointPen

    glyph_name = 'a'
    font_path = 'MyFont.ufo'

    font = Font(font_path)
    glyph = font[glyph_name]

    pen = RecordingPointPen()
    glyph.drawPoints(pen)
    print(pen.value)

    new_glyph = font.newGlyph('b')
    pen.replay(new_glyph.getPointPen())
    """

    def __init__(self):
        self.value = []

    def beginPath(self, **kwargs):
        self.value.append(("beginPath", (), kwargs))

    def endPath(self):
        self.value.append(("endPath", (), {}))

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        d = {}
        for k, v in kwargs.items():
            d[k] = 'None' if not v else v
        self.value.append(("addPoint", (pt, segmentType, smooth, name), d))

    def addComponent(self, baseGlyphName, transformation, **kwargs):
        self.value.append(("addComponent", (baseGlyphName, transformation), kwargs))

    def replay(self, pointPen):
        for operator, args, kwargs in self.value:
            getattr(pointPen, operator)(*args, **kwargs)

class RecordingPointPenCompact(AbstractPointPen):

    def __init__(self):
        self.value = []

    def beginPath(self, **kwargs):
        self.value.append(("beginPath"))

    def endPath(self):
        self.value.append(("endPath"))

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        # self.value.append(("addPoint", (pt, segmentType, smooth)))
        d = {"x":pt[0], "y":pt[1]}
        if segmentType:
            d["type"] = segmentType
        self.value.append(("point", d))

    def addComponent(self, baseGlyphName, transformation, **kwargs):
        self.value.append(("addComponent", (baseGlyphName, transformation)))

    # def addDeepComponent(self, glyphName, transformation, coord):
    #     self.value.append(("addDeepComponent", (glyphName, transformation, coord)))

    # def addGlyphVariationLayers(self, glyphVariationLayers: list):
    #     pass

    # def addVariationGlyphs(self, variationGlyphs: list):
    #     pass

    def replay(self, pointPen):
        for operator, args, kwargs in self.value:
            getattr(pointPen, operator)(*args, **kwargs)

if __name__ == "__main__":
    from fontTools.pens.basePen import _TestPen
    pen = RecordingPen()
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.curveTo((50, 75), (60, 50), (50, 25))
    pen.closePath()
    from pprint import pprint
    pprint(pen.value)
