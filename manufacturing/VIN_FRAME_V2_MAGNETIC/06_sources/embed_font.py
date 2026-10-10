from pathlib import Path
from fontTools.ttLib import TTCollection
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen

root=Path(__file__).resolve().parent
text=''.join((root/n).read_text() for n in ['build_package.py','manual.md'])
text+=''.join(chr(i) for i in range(32,127))
collection=TTCollection('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
font=collection.fonts[2]
opt=subset.Options();opt.name_IDs=['*'];opt.notdef_glyph=True;opt.notdef_outline=True
ss=subset.Subsetter(options=opt);ss.populate(text=text);ss.subset(font)
gs=font.getGlyphSet(); glyphs={}
for name in font.getGlyphOrder():
    pen=TTGlyphPen(gs);curve=Cu2QuPen(pen,max_err=1.0,reverse_direction=True)
    gs[name].draw(curve);glyphs[name]=pen.glyph()
fb=FontBuilder(font['head'].unitsPerEm,isTTF=True)
fb.setupGlyphOrder(font.getGlyphOrder());fb.setupCharacterMap(font.getBestCmap());fb.setupGlyf(glyphs)
fb.setupHorizontalMetrics(font['hmtx'].metrics)
fb.setupHorizontalHeader(ascent=font['hhea'].ascent,descent=font['hhea'].descent)
fb.setupNameTable({'familyName':'VIN SC Subset','styleName':'Regular','uniqueFontIdentifier':'VINSCSubsetRevB','fullName':'VIN SC Subset Regular','psName':'VINSCSubset-Regular','version':'Version 1.0','copyright':'Subset derived from Noto Sans CJK, SIL Open Font License 1.1','licenseDescription':'SIL Open Font License 1.1','licenseInfoURL':'https://openfontlicense.org/'})
fb.setupOS2(sTypoAscender=font['OS/2'].sTypoAscender,sTypoDescender=font['OS/2'].sTypoDescender,usWinAscent=font['OS/2'].usWinAscent,usWinDescent=font['OS/2'].usWinDescent)
fb.setupPost();fb.setupMaxp();fb.save(root/'cjk_embed.ttf')
print('Embedded-font subset generated:',len(glyphs),'glyphs')
