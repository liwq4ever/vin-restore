from pathlib import Path
import json, csv, math, hashlib, shutil, zipfile, datetime
import numpy as np
import cv2
import cadquery as cq
import ezdxf
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'VIN_FRAME_V1'
for d in ['01_drawings','02_cad','03_artwork','04_calibration','05_printed_handles','06_sources']:
    (OUT/d).mkdir(parents=True,exist_ok=True)
W,H,T=260.,70.,3.
WIN=(20.,20.,220.,30.)
PADS=[(10.,10.),(250.,10.),(130.,60.)]
MOUNTS=[(10.,22.),(10.,48.),(250.,22.),(250.,48.)]
if (ROOT/'cjk_embed.ttf').exists():
    pdfmetrics.registerFont(TTFont('STSong-Light',str(ROOT/'cjk_embed.ttf')))
else:
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

def rounded_box(w,h,t,r,x=0,y=0,z=0):
    return cq.Workplane('XY').box(w,h,t,centered=(False,False,False)).edges('|Z').fillet(r).translate((x,y,z))

def cylinder(x,y,z,r,h):
    return cq.Workplane('XY').workplane(offset=z).center(x,y).circle(r).extrude(h)

def build_body():
    b=rounded_box(W,H,T,4)
    b=b.cut(rounded_box(220,30,5,3,20,20,-1))
    for x,y in PADS:
        b=b.cut(cylinder(x,y,-.01,4.01,.21))
        # Geometric pilot only. Real M2x0.4 blind thread, 1.5 usable depth;
        # drill total depth 2.2 from pocket floor INCLUDING drill point.
        b=b.cut(cylinder(x,y,.2,.8,2.2))
    for x,y in MOUNTS:
        # Geometric pilot only. M3x0.5 blind thread from top, usable depth 1.5;
        # drill total depth 2.5 INCLUDING drill point.
        b=b.cut(cylinder(x,y,.5,1.25,2.51))
    return b

def build_pad():
    p=cylinder(0,0,0,3.99,1.5).cut(cylinder(0,0,-.01,1.1,1.52))
    cone=cq.Solid.makeCone(2.15,1.1,1.05)
    return p.cut(cq.Workplane('XY').newObject([cone]))

def build_handle():
    # Local z=0 rests on plate FRONT z=3.0. Never used as a contact datum.
    a=cq.Workplane('XY').box(30,8,3,centered=(False,False,False)).translate((-15,18,0))
    a=a.union(cq.Workplane('XY').box(30,8,3,centered=(False,False,False)).translate((-15,44,0)))
    a=a.union(cq.Workplane('XY').box(8,34,15,centered=(False,False,False)).translate((-15,18,0)))
    for x,y in [(10,22),(10,48)]: a=a.cut(cylinder(x,y,-.1,1.7,3.2))
    return a

body,pad,handle=build_body(),build_pad(),build_handle()
for model in [body,pad,handle]:
    assert model.val().isValid() and len(model.solids().vals())==1
cq.exporters.export(body,str(OUT/'02_cad/metal_frame.step'))
cq.exporters.export(pad,str(OUT/'02_cad/peek_contact_pad.step'))
cq.exporters.export(handle,str(OUT/'05_printed_handles/handle.step'))
cq.exporters.export(handle,str(OUT/'05_printed_handles/handle.stl'),tolerance=.05,angularTolerance=.1)
assy=cq.Assembly(name='VIN_FRAME_V1')
assy.add(body,name='316L_body',color=cq.Color(.68,.71,.74))
for i,(x,y) in enumerate(PADS):
    assy.add(pad,name=f'PEEK_pad_{i+1}',loc=cq.Location(cq.Vector(x,y,-1.3)),color=cq.Color(.78,.65,.43))
assy.add(handle,name='optional_handle_left',loc=cq.Location(cq.Vector(0,0,3)),color=cq.Color(.12,.35,.55))
assy.add(handle,name='optional_handle_right',loc=cq.Location(cq.Vector(260,70,3),cq.Vector(0,0,1),180),color=cq.Color(.12,.35,.55))
assy.save(str(OUT/'02_cad/assembly_nominal.step'))

# DXF coordinates: mm, lower-left origin, X right, Y up. No tool offsets.
def rounded_poly(msp,x,y,w,h,r,layer):
    k=math.tan(math.pi/8)
    v=[(x+r,y,0),(x+w-r,y,k),(x+w,y+r,0),(x+w,y+h-r,k),
       (x+w-r,y+h,0),(x+r,y+h,k),(x,y+h-r,0),(x,y+r,k)]
    msp.add_lwpolyline(v,format='xyb',close=True,dxfattribs={'layer':layer})

doc=ezdxf.new('R2010'); doc.units=ezdxf.units.MM
for layer,col in [('CUT_OUTER',7),('CUT_WINDOW',1),('BOTTOM_POCKET_D8_02',3),('BOTTOM_M2_BLIND',4),('TOP_M3_BLIND',5)]:
    doc.layers.new(layer,dxfattribs={'color':col})
msp=doc.modelspace(); rounded_poly(msp,0,0,W,H,4,'CUT_OUTER'); rounded_poly(msp,*WIN,3,'CUT_WINDOW')
for x,y in PADS:
    msp.add_circle((x,y),4.01,dxfattribs={'layer':'BOTTOM_POCKET_D8_02'})
    msp.add_circle((x,y),.8,dxfattribs={'layer':'BOTTOM_M2_BLIND'})
for x,y in MOUNTS: msp.add_circle((x,y),1.25,dxfattribs={'layer':'TOP_M3_BLIND'})
doc.saveas(OUT/'02_cad/metal_frame_operations.dxf')
# A profile-only file prevents a laser/waterjet operator treating blind holes as through cuts.
prof=ezdxf.new('R2010'); prof.units=ezdxf.units.MM
prof.layers.new('CUT',dxfattribs={'color':7}); pm=prof.modelspace()
rounded_poly(pm,0,0,W,H,4,'CUT'); rounded_poly(pm,*WIN,3,'CUT')
prof.saveas(OUT/'02_cad/rough_cut_profile_only.dxf')

DICT=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
tag_centers=[(x,60.) for x in [30,70,110,150,190,230]]+[(x,10.) for x in [30,70,110,150,190,230]]+[(10.,35.),(250.,35.)]
tiles=[(x,y) for y in [60.,10.] for x in [50,90,130,170,210]]
black=[]; features=[]; tags=[]
corner_labels=['TL','TR','BR','BL']
for tag_id,(x,y) in enumerate(tag_centers):
    bits=cv2.aruco.generateImageMarker(DICT,tag_id,6,borderBits=1)
    x0,y0=x-6,y-6
    for row in range(6):
        for col in range(6):
            if bits[row,col]==0: black.append((x0+col*2,y0+(5-row)*2,2.,2.))
    cs=[(x0,y0+12),(x0+12,y0+12),(x0+12,y0),(x0,y0)]
    tags.append({'id':tag_id,'center_xy_mm':[x,y],'corners_xy_mm':cs,'corner_order':corner_labels})
    for lab,(xx,yy) in zip(corner_labels,cs):
        features.append({'feature_id':f'A{tag_id:02d}_{lab}','type':'aruco_corner','marker_id':tag_id,'x_mm':xx,'y_mm':yy,'z_mm':4.3})
for ti,(x,y) in enumerate(tiles):
    for row in range(2):
        for col in range(4):
            if (row+col)%2==0: black.append((x-6+col*3,y-3+(1-row)*3,3.,3.))
    for ci,xx in enumerate([x-3,x,x+3]):
        features.append({'feature_id':f'C{ti:02d}_{ci}','type':'checker_corner','tile_id':ti,'x_mm':xx,'y_mm':y,'z_mm':4.3})

# Production black-layer SVG: no text, dimensions or registration crosses.
svg=['<?xml version="1.0" encoding="UTF-8"?>', '<svg xmlns="http://www.w3.org/2000/svg" width="260mm" height="70mm" viewBox="0 0 260 70">',
     '<title>VIN-FRAME-V1 BLACK FILLED AREAS; mm; camera-side view; no mirror</title>', '<g fill="#000000" stroke="none">']
svg += [f'<rect x="{x:g}" y="{H-y-h:g}" width="{w:g}" height="{h:g}"/>' for x,y,w,h in black]
svg += ['</g></svg>']; (OUT/'03_artwork/black_pattern_1to1.svg').write_text('\n'.join(svg),encoding='utf-8')
bd=ezdxf.new('R2010'); bd.units=ezdxf.units.MM
bd.layers.new('BLACK_FILLED_AREAS',dxfattribs={'color':7}); bm=bd.modelspace()
for x,y,w,h in black:
    hatch=bm.add_hatch(color=7,dxfattribs={'layer':'BLACK_FILLED_AREAS'})
    hatch.paths.add_polyline_path([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],is_closed=True)
bd.saveas(OUT/'03_artwork/black_pattern_filled.dxf')
# Raster is convenience only; vector is authoritative manufacturing artwork.
PPM=60
im=Image.new('L',(int(W*PPM),int(H*PPM)),255); dr=ImageDraw.Draw(im)
for x,y,w,h in black:
    a,b,c,d=round(x*PPM),round((H-y-h)*PPM),round((x+w)*PPM)-1,round((H-y)*PPM)-1
    dr.rectangle((a,b,c,d),fill=0)
im.save(OUT/'03_artwork/pattern_1524ppi.png',dpi=(1524,1524))

nominal={
    'schema':'vin_reference_frame_nominal_v1','design_id':'VIN-FRAME-V1','revision':'A',
    'units':'mm','calibration_status':'NOMINAL_ONLY_NOT_VALID_FOR_PRODUCTION',
    'coordinate_system':'Origin XY at nominal lower-left of plate front-view outline; X right, Y up; Z=0 is assembled contact datum plane, +Z toward camera.',
    'cad_to_this_coordinate_system':'X=Xcad; Y=Ycad; Z=Zcad+1.3 (nominal only)',
    'plate_size_mm':[W,H,T],'window_xywh_mm':list(WIN),
    'nominal_height_contact_to_marker_mm':4.3,'height_excludes_coating':True,
    'reference_temperature_C':20,'nominal_cte_per_K':16e-6,'cte_is_material_datasheet_value_not_individual_certificate':True,
    'dictionary':'DICT_4X4_50','marker_border_bits':1,'marker_black_square_size_mm':12,
    'quiet_zone_min_mm':2,'markers':tags,'features':features,
    'pad_centers_xy_mm':PADS,'mount_centers_xy_mm':MOUNTS,
    'requirement':'Replace nominal feature xyz and height by measured, serial-specific values. Do not set calibrated=true from CAD.'
}
(OUT/'04_calibration/nominal_geometry.json').write_text(json.dumps(nominal,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'04_calibration/as_built_measurement_template.csv').open('w',newline='',encoding='utf-8-sig') as f:
    wr=csv.writer(f); wr.writerow(['feature_id','nominal_x_mm','nominal_y_mm','nominal_z_mm','measured_x_mm','measured_y_mm','measured_z_mm','expanded_uncertainty_mm','temperature_C','frame_serial','instrument','operator','date'])
    for p in features: wr.writerow([p['feature_id'],p['x_mm'],p['y_mm'],p['z_mm'],'','','','','','','','',''])
    for i,(x,y) in enumerate(PADS): wr.writerow([f'CONTACT_P{i+1}',x,y,0,'','','','','','','','',''])

# Verify dictionary, all 14 tags, coordinates and manufacturing keep-out areas.
small=cv2.resize(np.array(im),(2600,700),interpolation=cv2.INTER_AREA)
dp=cv2.aruco.DetectorParameters(); dp.cornerRefinementMethod=cv2.aruco.CORNER_REFINE_SUBPIX
det=cv2.aruco.ArucoDetector(DICT,dp)
corners,ids,rejected=det.detectMarkers(small)
assert ids is not None and set(ids.ravel())==set(range(14)),f'Detection failed: {ids}'
max_corner_error=0
for c,tag_id in zip(corners,ids.ravel()):
    expected=np.array(tags[int(tag_id)]['corners_xy_mm'])
    expected[:,1]=H-expected[:,1]; expected*=10
    # Rendering coordinates describe pixel-cell boundaries; OpenCV reports
    # pixel-center coordinates, so add 0.5 only for this synthetic comparison.
    max_corner_error=max(max_corner_error,float(np.max(np.linalg.norm(c[0]+.5-expected,axis=1))))
assert max_corner_error<=2
for x,y,w,h in black:
    assert x>=2 and y>=2 and x+w<=W-2 and y+h<=H-2
    assert not (x<240 and x+w>20 and y<50 and y+h>20), 'Pattern crosses opening'
    for mx,my in MOUNTS:
        # Exclude screw/tab footprint [mx-5,mx+5] x [my-4,my+4].
        assert not (x<mx+5 and x+w>mx-5 and y<my+4 and y+h>my-4)
assert len(features)==86

# PDF technical drawing helpers (all page coordinates below in mm).
def text(c,x,y,s,size=9,font='STSong-Light'):
    c.setFont(font,size); c.drawString(x*mm,y*mm,s)
def line(c,x1,y1,x2,y2): c.line(x1*mm,y1*mm,x2*mm,y2*mm)
def circle(c,x,y,r): c.circle(x*mm,y*mm,r*mm,stroke=1,fill=0)
def rect(c,x,y,w,h,fill=0): c.rect(x*mm,y*mm,w*mm,h*mm,stroke=1,fill=fill)
def title(c,name,sheet):
    c.setLineWidth(.3*mm); rect(c,10,10,400,277)
    text(c,18,277,name,15); text(c,18,268,'VIN-FRAME-V1 / REV A / 样件加工评审版，未进行实体精度验证',10)
    line(c,10,35,410,35)
    text(c,18,25,'单位 mm | 数值尺寸优先，禁止从图上量尺寸 | STEP不含真实螺纹及涂层',9)
    text(c,18,17,'坐标：正面左下角X=0,Y=0；X向右、Y向上。所有孔位按正面XY定位。',9)
    text(c,340,20,f'A3 / Sheet {sheet}/4',10,'Helvetica')
def dimh(c,x1,x2,y,origin_y,label):
    c.setLineWidth(.15*mm); line(c,x1,origin_y,x1,y+2);line(c,x2,origin_y,x2,y+2);line(c,x1,y,x2,y)
    line(c,x1-1,y-1,x1+1,y+1);line(c,x2-1,y-1,x2+1,y+1)
    c.setFont('Helvetica',9);c.drawCentredString((x1+x2)/2*mm,(y+2)*mm,label)
def dimv(c,y1,y2,x,origin_x,label):
    line(c,origin_x,y1,x-2,y1);line(c,origin_x,y2,x-2,y2);line(c,x,y1,x,y2)
    line(c,x-1,y1-1,x+1,y1+1);line(c,x-1,y2-1,x+1,y2+1)
    text(c,x-16,(y1+y2)/2,label,9,'Helvetica')
def frame_view(c,x,y,pattern=False,pads=False,mounts=False):
    c.setLineWidth(.25*mm);c.roundRect(x*mm,y*mm,260*mm,70*mm,4*mm,stroke=1,fill=0)
    c.roundRect((x+20)*mm,(y+20)*mm,220*mm,30*mm,3*mm,stroke=1,fill=0)
    if pattern:
        c.setFillColor(colors.black)
        for xx,yy,w,h in black: c.rect((x+xx)*mm,(y+yy)*mm,w*mm,h*mm,stroke=0,fill=1)
    if pads:
        for i,(xx,yy) in enumerate(PADS):
            circle(c,x+xx,y+yy,4.01); circle(c,x+xx,y+yy,.8)
            text(c,x+xx-6,y+yy+7,f'P{i+1}',8,'Helvetica')
    if mounts:
        for xx,yy in MOUNTS: circle(c,x+xx,y+yy,1.25)

c=canvas.Canvas(str(OUT/'01_drawings/manufacturing_drawings_A3.pdf'),pagesize=(420*mm,297*mm))
c.setTitle('VIN参考框：金属框、接触垫、装配和标记图纸')
title(c,'金属参考框：外形及正面加工',1)
frame_view(c,55,180,mounts=True)
dimh(c,55,315,256,250,'260 +/-0.10');dimv(c,180,250,44,55,'70 +/-0.10')
dimh(c,75,295,167,200,'220 +/-0.10');dimv(c,200,230,335,295,'30 +/-0.10')
text(c,98,216,'中央开窗 / WINDOW',12);text(c,110,208,'内角R3 / 外角R4',9)
text(c,20,152,'材料：316L / EN 1.4404；成品金属厚度3.00±0.05；外形及开窗CNC精加工。',10)
text(c,20,142,'正面可选手柄安装孔：4×M3×0.5盲孔，有效牙深1.5；钻孔总深2.5（含钻尖）。',10)
text(c,20,132,'孔位（正面XY）：(10,22)、(10,48)、(250,22)、(250,48)，位置±0.10。',10)
text(c,20,122,'禁止打穿；STEP圆孔为底孔示意，实际攻丝按本图；不用手柄时孔可保留空置。',10)
text(c,20,112,'顶面完成涂层后光学区域平面度目标≤0.03；先由加工厂确认工艺和测量能力。',10)
text(c,20,102,'边缘去毛刺；外缘/窗口触及边C0.2~0.3，角部圆滑；不得磨损光学图形边缘。',10)
text(c,20,92,'上下表面稳定加工后再成像；不要仅激光切割后直接使用；不焊接、不折弯。',10)
text(c,20,82,'尺寸与平面度为样件要求；最终0.2毫米指标必须经过整套拍摄系统验收。',10)
text(c,20,62,'加工文件：metal_frame.step；粗切只用rough_cut_profile_only.dxf，盲孔另外加工。',10)
c.showPage()
title(c,'背面定位加工及PEEK接触垫',2)
frame_view(c,55,180,pads=True)
text(c,85,215,'背面特征按正面XY投影显示；不要镜像坐标。',10)
text(c,20,158,'P1=(10,10)，P2=(250,10)，P3=(130,60)；位置±0.10。',10)
text(c,20,148,'每处：背面定位浅窝Ø8.02 +0.02/0，深0.20±0.02；中央M2×0.4盲孔。',10)
text(c,20,138,'M2有效牙深1.5；从浅窝底钻孔总深2.2（含钻尖），不得贯穿正面。',10)
# Pad enlarged section: 8x, contact on bottom, metal seat on top.
sx,sy,sc=55,92,8
rect(c,sx,sy,7.98*sc,1.5*sc)
line(c,sx+2.89*sc,sy+1.05*sc,sx+1.84*sc,sy)
line(c,sx+5.09*sc,sy+1.05*sc,sx+6.14*sc,sy)
line(c,sx+2.89*sc,sy+1.05*sc,sx+2.89*sc,sy+1.5*sc)
line(c,sx+5.09*sc,sy+1.05*sc,sx+5.09*sc,sy+1.5*sc)
dimh(c,sx,sx+7.98*sc,sy-7,sy,'OD 7.98 +/-0.01')
dimv(c,sy,sy+1.5*sc,sx+7.98*sc+14,sx+7.98*sc,'1.50 +/-0.01')
text(c,55,115,'接触垫剖面 / 8:1 / CAD含沉头孔',10)
text(c,180,112,'材料：本色、未填充PEEK，CNC车削，不用3D打印。',10)
text(c,180,102,'通孔Ø2.20；接触侧沉头Ø4.30，90°，深1.05。',10)
text(c,180,92,'外径7.98±0.01，厚1.50±0.01；三片配组厚差≤0.01。',10)
text(c,180,82,'接触面平整、无毛刺；外缘轻微倒钝≤0.05。',10)
text(c,180,72,'螺钉：M2×3，90°沉头，头径≤4.20；头部低于接触面≥0.05。',10)
text(c,20,52,'低预紧装配并复测；垫片须贴合浅窝底，不加胶、泡棉或橡胶；更换后重新测量高度。',10)
c.showPage()
title(c,'装配关系及可选3D打印手柄',3)
text(c,20,249,'装配基准：三片PEEK垫的外侧接触面共同定义A平面；钢印周围基准面应与A重合。',11)
# Enlarged cross-section with exact nominal heights, scale 12 in z.
line(c,45,176,168,176); text(c,175,173,'A：车身接触/钢印基准面',10)
rect(c,75,191.6,65,36) # underside at +1.3, top at +4.3
rect(c,90,176,30,18)
text(c,45,236,'局部示意；竖向放大，非完整剖切图',9)
text(c,175,225,'标记面：A上方约4.30 mm＋成像层厚度',10)
text(c,175,213,'金属框下表面：A上方约1.30 mm',10)
text(c,175,201,'浅窝深0.20；PEEK垫厚1.50；金属厚3.00',10)
text(c,175,189,'高度h必须在最终装配/涂层完成后实测。',10)
text(c,20,156,'手柄：ASA优先，PETG用于室内打样；只作握持辅助，不承担尺寸和接触基准。',10)
text(c,20,145,'打印handle.stl两件；左件直接安装；右件绕Z转180°并移到(260,70)。',10)
text(c,20,134,'孔Ø3.4，安装面厚3.0；M3×5螺钉＋0.5毫米垫圈，设计进入金属约1.5。',10)
text(c,20,123,'必须核对真实螺钉长度、垫圈和打印厚度，避免盲孔顶底；仅轻紧，装配后复测。',10)
text(c,20,112,'打印件底面不得低于金属框底面；装配后与车身净间隙建议≥0.8。',10)
text(c,20,101,'手柄净空避开编码、棋盘角点及白色隔离区；握持时勿使参考框弯曲。',10)
text(c,20,90,'层高0.20，4道外壁，约35%填充；按耗材厂商参数打印，适配配合先试装。',10)
text(c,20,70,'首件可先不安装手柄，完成几何验证后再评估；装配STEP不含螺钉及成像涂层。',10)
text(c,20,55,'A面位置、角点XYZ、温度和测量不确定度必须进入每个框的实测档案。',10)
c.showPage()
title(c,'精密黑白图案：位置、方向与供应商注意事项',4)
frame_view(c,55,180,pattern=True)
text(c,130,215,'VIN-FRAME-V1  /  摄像头视角 / 不镜像',10)
for i,(x,y) in enumerate(tag_centers):
    if y==60: text(c,55+x-4,254,f'A{i:02}',8,'Helvetica')
    elif y==10: text(c,55+x-4,174,f'A{i:02}',8,'Helvetica')
    else: text(c,55+x-4,180+y+11,f'A{i:02}',8,'Helvetica')
text(c,20,156,'编码：DICT_4X4_50，ID 0~13；黑色外方框12×12，1格黑边，单元2×2。',10)
text(c,20,145,'每个编码外至少留2毫米纯白隔离区；编码不能旋转、镜像、重新描图或抗锯齿重采样。',10)
text(c,20,134,'棋盘条：10组，每组4列×2行，单格3毫米，图形12×6；每组3个内部角点，共30点。',10)
text(c,20,123,'正面白色哑光薄涂层＋黑色精密成像；丝印/光刻工艺先打样，成品光学边缘须测量。',10)
text(c,20,112,'图案尺寸定位目标±0.05；角点区域线边偏差/毛边目标≤0.03，需显微检查确认。',10)
text(c,20,101,'以SVG物理尺寸或DXF为成像母版；BLACK_FILLED_AREAS表示实心黑块，不能只画轮廓。',10)
text(c,20,90,'成像图层不得包含本图的文字、尺寸或外框线；编号刻在侧面，禁止覆盖隔离区。',10)
text(c,20,79,'本图仅用于位置核对；01图纸不是成像母版。普通打印贴纸仅用于识别试验。',10)
text(c,20,62,'正式软件必须读取成品实测坐标；nominal_geometry.json只供开发，不是校准证书。',10)
c.save()

# Exact-scale artwork PDF, wider custom page than A4 to preserve the 260mm width.
pc=canvas.Canvas(str(OUT/'03_artwork/black_pattern_1to1.pdf'),pagesize=(280*mm,90*mm))
pc.setTitle('VIN-FRAME-V1 BLACK ARTWORK 1:1 — 280x90 mm page')
pc.setFillColor(colors.black)
for x,y,w,h in black: pc.rect((10+x)*mm,(10+y)*mm,w*mm,h*mm,stroke=0,fill=1)
pc.save()

# Pattern QC overview, clear camera-side XY mapping.
preview=Image.fromarray(small).convert('RGB');pd=ImageDraw.Draw(preview)
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',28)
pd.rounded_rectangle([200,200,2400,500],radius=30,fill=(233,240,244),outline=(125,146,157),width=2)
pd.text((650,295),'中央开窗 220 × 30 mm',font=font,fill=(50,69,83))
for i,(x,y) in enumerate(tag_centers):
    if y==60: pd.text((int(x*10)-18,0),str(i),font=font,fill=(30,70,115))
    elif y==10: pd.text((int(x*10)-18,660),str(i),font=font,fill=(30,70,115))
preview.save(OUT/'01_drawings/pattern_overview.png')

# Colored engineering illustration with optical artwork projected on top face.
font_large=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',34)
ill=Image.new('RGB',(1500,750),(248,250,252)); dd=ImageDraw.Draw(ill)
def project(x,y,z): return (250+4*(.96*x-.48*y),515+4*(.14*x-.48*y-2*z))
def poly3(points,fill,outline=(105,121,130)):
    dd.polygon([project(*p) for p in points],fill=fill,outline=outline,width=2)
poly3([(0,0,0),(260,0,0),(260,0,3),(0,0,3)],(136,150,159))
poly3([(260,0,0),(260,70,0),(260,70,3),(260,0,3)],(152,166,173))
poly3([(0,0,3),(260,0,3),(260,70,3),(0,70,3)],(242,244,240))
poly3([(20,20,3),(240,20,3),(240,50,3),(20,50,3)],(221,230,235))
for x,y,w,h in black: poly3([(x,y,3.05),(x+w,y,3.05),(x+w,y+h,3.05),(x,y+h,3.05)],(23,27,30),None)
for x,y in PADS:
    px,py=project(x,y,-1.3); dd.ellipse((px-12,py-5,px+12,py+5),fill=(200,172,115),outline=(125,105,75))
dd.text((65,35),'VIN参考框 V1｜样件结构示意',font=font_large,fill=(27,49,65))
dd.text((65,95),'316L金属基准框 · 背面三点PEEK接触 · 已知高度差补偿',font=font,fill=(55,77,92))
dd.text((65,630),'图案位置来自文件；示意图不表达加工公差。可选打印手柄见STEP/STL。',font=font,fill=(55,77,92))
ill.save(OUT/'01_drawings/assembly_preview.png')

SCAD='''// VIN-FRAME-V1 Rev A. Units mm; CAD Z=0 at metal underside.
// Reference contact plane Z=-1.3; nominal marker Z=3 + coating.
// Pilot holes are simplified, NOT modeled threads. Refer to PDF for blind drilling.
$fn=64;
part="assembly"; // "body", "pad", "handle", "assembly"
module rr(w,h,r,z){ linear_extrude(height=z) hull(){for(x=[r,w-r])for(y=[r,h-r])translate([x,y])circle(r=r);} }
module body(){difference(){rr(260,70,4,3);translate([20,20,-1])rr(220,30,3,5);
for(p=[[10,10],[250,10],[130,60]]){translate([p[0],p[1],-.01])cylinder(d=8.02,h=.21);translate([p[0],p[1],.2])cylinder(d=1.6,h=2.2);}
for(p=[[10,22],[10,48],[250,22],[250,48]])translate([p[0],p[1],.5])cylinder(d=2.5,h=2.51);}}
module pad(){difference(){cylinder(d=7.98,h=1.5);translate([0,0,-.01])cylinder(d=2.2,h=1.52);cylinder(d1=4.3,d2=2.2,h=1.05);}}
module handle(){difference(){union(){translate([-15,18,0])cube([30,8,3]);translate([-15,44,0])cube([30,8,3]);translate([-15,18,0])cube([8,34,15]);}for(p=[[10,22],[10,48]])translate([p[0],p[1],-.1])cylinder(d=3.4,h=3.2);}}
if(part=="body")body();if(part=="pad")pad();if(part=="handle")handle();
if(part=="assembly"){color("silver")body();for(p=[[10,10],[250,10],[130,60]])color("tan")translate([p[0],p[1],-1.3])pad();color("steelblue")translate([0,0,3])handle();color("steelblue")translate([260,70,3])rotate([0,0,180])handle();}
'''
(OUT/'06_sources/frame_parametric.scad').write_text(SCAD,encoding='utf-8')

checks={
 'generated_at':'2026-10-10','status':'DIGITAL_FILES_CHECKED_PHYSICAL_PROTOTYPE_NOT_TESTED',
 'cadquery':cq.__version__,'opencv':cv2.__version__,
 'cad_solids_valid':True,'models':['metal_frame','peek_contact_pad','handle'],
 'body_bbox_mm':[round(body.val().BoundingBox().xlen,4),round(body.val().BoundingBox().ylen,4),round(body.val().BoundingBox().zlen,4)],
 'body_volume_mm3':round(body.val().Volume(),3),'estimated_body_mass_g_at_8g_cm3':round(body.val().Volume()*.008,1),
 'nominal_geometry_feature_count':len(features),'aruco_ids_detected':sorted(map(int,ids.ravel())),
 'synthetic_detection_scale_px_per_mm':10,'synthetic_max_corner_error_px':round(max_corner_error,4),
 'synthetic_comparison_pixel_convention':'OpenCV pixel centers +0.5 compared with rendered pixel-cell boundaries; not an App processing prescription',
 'synthetic_test_is_not_physical_accuracy_validation':True,'artwork_does_not_cross_window_or_handle_mount_footprints':True,
 'limitations':['CAD is nominal, not as-built calibration','No physical flatness or contact test','No camera or system 0.2mm accuracy validation','No manufacturing supplier review','Coatings, screw threads and screws not modeled']
}
(OUT/'digital_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))

