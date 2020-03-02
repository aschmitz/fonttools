# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod

from fontTools.misc.py23 import *
from fontTools.misc.textTools import safeEval
from . import DefaultTable


class table_C_O_L_R_(DefaultTable.DefaultTable):

	""" This table is structured so that you can treat it like a dictionary keyed by glyph name.
	ttFont['COLR'][<glyphName>] will return the color layers for any glyph
	ttFont['COLR'][<glyphName>] = <value> will set the color layers for any glyph.
	"""

	def decompile(self, data, ttFont):
		from .otBase import OTTableReader
		from . import otTables

		reader = OTTableReader(data, tableTag=self.tableTag)
		tableClass = getattr(otTables, self.tableTag)
		table = tableClass()
		table.decompile(reader, ttFont)

		self.version = table.Version
		assert (self.version == 0), "Version of COLR table is higher than I know how to handle"

		self.ColorLayers = colorLayerLists = {}

		layerRecords = table.LayerRecordArray.LayerRecord
		numLayerRecords = len(layerRecords)
		for baseRec in table.BaseGlyphRecordArray.BaseGlyphRecord:
			baseGlyph = baseRec.BaseGlyph
			firstLayerIndex = baseRec.FirstLayerIndex
			numLayers = baseRec.NumLayers
			assert (firstLayerIndex + numLayers <= numLayerRecords)
			layers = []
			for i in range(firstLayerIndex, firstLayerIndex+numLayers):
				layerRec = layerRecords[i]
				layers.append(LayerRecord(layerRec.LayerGlyph, layerRec.PaletteIndex))
			colorLayerLists[baseGlyph] = layers

	def compile(self, ttFont):
		from .otBase import OTTableWriter
		from . import otTables

		ttFont.getReverseGlyphMap(rebuild=True)

		tableClass = getattr(otTables, self.tableTag)
		table = tableClass()

		table.Version = self.version

		table.BaseGlyphRecordArray = otTables.BaseGlyphRecordArray()
		table.BaseGlyphRecordArray.BaseGlyphRecord = baseGlyphRecords = []
		table.LayerRecordArray = otTables.LayerRecordArray()
		table.LayerRecordArray.LayerRecord = layerRecords = []

		for baseGlyph in sorted(self.ColorLayers.keys(), key=ttFont.getGlyphID):
			layers = self.ColorLayers[baseGlyph]

			baseRec = otTables.BaseGlyphRecord()
			baseRec.BaseGlyph = baseGlyph
			baseRec.FirstLayerIndex = len(layerRecords)
			baseRec.NumLayers = len(layers)
			baseGlyphRecords.append(baseRec)

			for layer in layers:
				layerRec = otTables.LayerRecord()
				layerRec.LayerGlyph = layer.name
				layerRec.PaletteIndex = layer.colorID
				layerRecords.append(layerRec)

		writer = OTTableWriter(tableTag=self.tableTag)
		table.compile(writer, ttFont)
		return writer.getAllData()

	def toXML(self, writer, ttFont):
		writer.simpletag("version", value=self.version)
		writer.newline()
		for baseGlyph in sorted(self.ColorLayers.keys(), key=ttFont.getGlyphID):
			writer.begintag("ColorGlyph", name=baseGlyph)
			writer.newline()
			for layer in self.ColorLayers[baseGlyph]:
				layer.toXML(writer, ttFont)
			writer.endtag("ColorGlyph")
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if not hasattr(self, "ColorLayers"):
			self.ColorLayers = {}
		if name == "ColorGlyph":
			glyphName = attrs["name"]
			for element in content:
				if isinstance(element, basestring):
					continue
			layers = []
			for element in content:
				if isinstance(element, basestring):
					continue
				layer = LayerRecord()
				layer.fromXML(element[0], element[1], element[2], ttFont)
				layers.append (layer)
			self[glyphName] = layers
		elif "value" in attrs:
			setattr(self, name, safeEval(attrs["value"]))

	def __getitem__(self, glyphName):
		if not isinstance(glyphName, str):
			raise TypeError(f"expected str, found {type(glyphName).__name__}")
		return self.ColorLayers[glyphName]

	def __setitem__(self, glyphName, value):
		if not isinstance(glyphName, str):
			raise TypeError(f"expected str, found {type(glyphName).__name__}")
		if value is not None:
			self.ColorLayers[glyphName] = value
		elif glyphName in self.ColorLayers:
			del self.ColorLayers[glyphName]

	def __delitem__(self, glyphName):
		del self.ColorLayers[glyphName]

class LayerRecord(object):

	def __init__(self, name=None, colorID=None):
		self.name = name
		self.colorID = colorID

	def toXML(self, writer, ttFont):
		writer.simpletag("layer", name=self.name, colorID=self.colorID)
		writer.newline()

	def fromXML(self, eltname, attrs, content, ttFont):
		for (name, value) in attrs.items():
			if name == "name":
				if isinstance(value, int):
					value = ttFont.getGlyphName(value)
				setattr(self, name, value)
			else:
				setattr(self, name, safeEval(value))
