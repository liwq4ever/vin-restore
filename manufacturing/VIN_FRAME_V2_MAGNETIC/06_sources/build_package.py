from pathlib import Path
import json, csv, math, hashlib, shutil, zipfile
import cadquery as cq
import ezdxf
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'VIN_FRAME_V2_MAGNETIC'
for d in ['01_drawings','02_cad','03_artwork','04_calibration','05_printed_handles','06_sources']:
    (OUT/d).mkdir(parents=True,exist_ok=True)
W,H,T=260.,70.,6.
PADS=[(14.,11.),(246.,11.),(130.,60.)]
MOUNTS=[(10.,22.),(10.,48.),(250.,22.),(250.,48.)]
PAD_T=1.9; POCKET=.2; PROJECTION=PAD_T-POCKET
MAG_T=1.5; BOND_T=.1; HEIGHT=T+PROJECTION
pdfmetrics.registerFont(TTFont('CJK',str(ROOT/'cjk_embed.ttf')))

def rr(w,h,t,r,x=0,y=0,z=0):
    return cq.Workplane('XY').box(w,h,t,centered=(False,False,False)).edges('|Z').fillet(r).translate((x,y,z))
def cyl(x,y,z,r,h):
    return cq.Workplane('XY').workplane(offset=z).center(x,y).circle(r).extrude(h)
body=rr(W,H,T,4).cut(rr(220,30,T+2,3,20,20,-1))
for x,y in PADS:
    body=body.cut(cyl(x,y,-.01,4.01,.21)).cut(cyl(x,y,.2,.8,3.4))
for x,y in MOUNTS:
    body=body.cut(cyl(x,y,2.5,1.25,3.51))
pad=cyl(0,0,0,3.99,PAD_T).cut(cyl(0,0,-.01,1.1,PAD_T+.02))
pad=pad.cut(cq.Workplane('XY').newObject([cq.Solid.makeCone(2.15,1.1,1.05)]))
mag=rr(24,16,MAG_T,1,-12,-8,0).cut(cyl(0,0,-.01,5,MAG_T+.02))
bond=rr(24,16,BOND_T,1,-12,-8,0).cut(cyl(0,0,-.01,5,BOND_T+.02))
handle=cq.Workplane('XY').box(30,8,3,centered=(False,False,False)).translate((-15,18,0))
handle=handle.union(cq.Workplane('XY').box(30,8,3,centered=(False,False,False)).translate((-15,44,0)))
handle=handle.union(cq.Workplane('XY').box(8,34,15,centered=(False,False,False)).translate((-15,18,0)))
for x,y in [(10,22),(10,48)]: handle=handle.cut(cyl(x,y,-.1,1.7,3.2))
models={'g10_frame':body,'peek_contact_pad':pad,'magnetic_tile':mag,'bond_layer_nominal':bond}
for name,obj in models.items():
    assert obj.val().isValid() and len(obj.solids().vals())==1
    cq.exporters.export(obj,str(OUT/'02_cad'/f'{name}.step'))
cq.exporters.export(handle,str(OUT/'05_printed_handles/handle.step'))
cq.exporters.export(handle,str(OUT/'05_printed_handles/handle.stl'),tolerance=.05,angularTolerance=.1)
assy=cq.Assembly(name='VIN_FRAME_V2_MAGNETIC')
assy.add(body,name='G10_CNC_body',color=cq.Color(.45,.61,.39))
for i,(x,y) in enumerate(PADS):
    assy.add(pad,name=f'PEEK_pad_{i+1}',loc=cq.Location(cq.Vector(x,y,-PROJECTION)),color=cq.Color(.83,.72,.5))
    assy.add(bond,name=f'bond_layer_{i+1}',loc=cq.Location(cq.Vector(x,y,-BOND_T)),color=cq.Color(.85,.85,.85))
    assy.add(mag,name=f'magnetic_tile_{i+1}',loc=cq.Location(cq.Vector(x,y,-MAG_T-BOND_T)),color=cq.Color(.18,.18,.18))
assy.add(handle,name='optional_left_handle',loc=cq.Location(cq.Vector(0,0,T)),color=cq.Color(.17,.38,.59))
assy.add(handle,name='optional_right_handle',loc=cq.Location(cq.Vector(260,70,T),cq.Vector(0,0,1),180),color=cq.Color(.17,.38,.59))
assy.save(str(OUT/'02_cad/assembly_nominal.step'))

def outline(m,x,y,w,h,r,layer):
    k=math.tan(math.pi/8)
    v=[(x+r,y,0),(x+w-r,y,k),(x+w,y+r,0),(x+w,y+h-r,k),(x+w-r,y+h,0),(x+r,y+h,k),(x,y+h-r,0),(x,y+r,k)]
    m.add_lwpolyline(v,format='xyb',close=True,dxfattribs={'layer':layer})
def dxf_file(name,layers):
    d=ezdxf.new('R2010');d.units=ezdxf.units.MM
    for i,l in enumerate(layers): d.layers.new(l,dxfattribs={'color':i%6+1})
    return d,d.modelspace()
d,m=dxf_file('frame',['OUTER','WINDOW','BOTTOM_POCKET_D8_02','BOTTOM_M2_BLIND','TOP_M3_BLIND'])
outline(m,0,0,W,H,4,'OUTER');outline(m,20,20,220,30,3,'WINDOW')
for x,y in PADS:
    m.add_circle((x,y),4.01,dxfattribs={'layer':'BOTTOM_POCKET_D8_02'})
    m.add_circle((x,y),.8,dxfattribs={'layer':'BOTTOM_M2_BLIND'})
for x,y in MOUNTS: m.add_circle((x,y),1.25,dxfattribs={'layer':'TOP_M3_BLIND'})
d.saveas(OUT/'02_cad/g10_frame_operations.dxf')
d,m=dxf_file('rough',['CUT']);outline(m,0,0,W,H,4,'CUT');outline(m,20,20,220,30,3,'CUT')
d.saveas(OUT/'02_cad/rough_cut_profile_only.dxf')
d,m=dxf_file('tile',['MAGNET_CUT','DATUM_NOT_CUT'])
outline(m,-12,-8,24,16,1,'MAGNET_CUT');m.add_circle((0,0),5,dxfattribs={'layer':'MAGNET_CUT'})
d.saveas(OUT/'02_cad/magnetic_tile_cut_1to1.dxf')
d,m=dxf_file('layout',['FRAME_REFERENCE_NOT_CUT','MAGNET_PLACEMENT_NOT_CUT','PAD_REFERENCE_NOT_CUT'])
outline(m,0,0,W,H,4,'FRAME_REFERENCE_NOT_CUT');outline(m,20,20,220,30,3,'FRAME_REFERENCE_NOT_CUT')
for x,y in PADS:
    outline(m,x-12,y-8,24,16,1,'MAGNET_PLACEMENT_NOT_CUT')
    m.add_circle((x,y),5,dxfattribs={'layer':'MAGNET_PLACEMENT_NOT_CUT'})
    m.add_circle((x,y),3.99,dxfattribs={'layer':'PAD_REFERENCE_NOT_CUT'})
d.saveas(OUT/'02_cad/back_layout_front_xy_not_mirrored.dxf')

DICT=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
tag_centers=[(x,60.) for x in [30,70,110,150,190,230]]+[(x,10.) for x in [30,70,110,150,190,230]]+[(10.,35.),(250.,35.)]
tiles=[(x,y) for y in [60.,10.] for x in [50,90,130,170,210]]
black=[];features=[];tags=[]
for tag_id,(x,y) in enumerate(tag_centers):
    bits=cv2.aruco.generateImageMarker(DICT,tag_id,6,borderBits=1)
    for row in range(6):
        for col in range(6):
            if bits[row,col]==0:black.append((x-6+col*2,y-6+(5-row)*2,2.,2.))
    cs=[(x-6,y+6),(x+6,y+6),(x+6,y-6),(x-6,y-6)]
    tags.append({'id':tag_id,'center_xy_mm':[x,y],'corners_xy_mm':cs,'corner_order':['TL','TR','BR','BL']})
    for lab,(xx,yy) in zip(['TL','TR','BR','BL'],cs):features.append({'feature_id':f'A{tag_id:02d}_{lab}','type':'aruco_corner','marker_id':tag_id,'x_mm':xx,'y_mm':yy,'z_mm':HEIGHT})
for ti,(x,y) in enumerate(tiles):
    for row in range(2):
        for col in range(4):
            if (row+col)%2==0:black.append((x-6+col*3,y-3+(1-row)*3,3.,3.))
    for ci,xx in enumerate([x-3,x,x+3]):features.append({'feature_id':f'C{ti:02d}_{ci}','type':'checker_corner','tile_id':ti,'x_mm':xx,'y_mm':y,'z_mm':HEIGHT})
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="260mm" height="70mm" viewBox="0 0 260 70">','<title>VIN V2 magnetic frame; camera-side view; mm; black filled areas; white background applied separately</title>','<g fill="black" stroke="none">']
svg += [f'<rect x="{x:g}" y="{H-y-h:g}" width="{w:g}" height="{h:g}"/>' for x,y,w,h in black]
(OUT/'03_artwork/black_pattern_1to1.svg').write_text('\n'.join(svg+['</g></svg>']))
d,m=dxf_file('black',['BLACK_FILLED_AREAS'])
for x,y,w,h in black:
    hatch=m.add_hatch(color=7,dxfattribs={'layer':'BLACK_FILLED_AREAS'});hatch.paths.add_polyline_path([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],is_closed=True)
d.saveas(OUT/'03_artwork/black_pattern_filled.dxf')
im=Image.new('L',(15600,4200),255);dr=ImageDraw.Draw(im)
for x,y,w,h in black:dr.rectangle((round(x*60),round((H-y-h)*60),round((x+w)*60)-1,round((H-y)*60)-1),fill=0)
im.save(OUT/'03_artwork/pattern_1524ppi.png',dpi=(1524,1524))
pc=canvas.Canvas(str(OUT/'03_artwork/black_pattern_1to1.pdf'),pagesize=(280*mm,90*mm))
for x,y,w,h in black:pc.rect((10+x)*mm,(10+y)*mm,w*mm,h*mm,stroke=0,fill=1)
pc.save()

nominal={'schema':'vin_reference_frame_nominal_v2','design_id':'VIN-FRAME-V2-MAGNETIC','revision':'A','units':'mm','calibration_status':'NOMINAL_ONLY_NOT_VALID_FOR_PRODUCTION','coordinate_system':'Origin XY at lower-left of front-view outline; X right; Y up; Z=0 assembled hard-contact datum A; +Z toward camera.','cad_to_this_coordinate_system':'Z=Zcad+1.7 NOMINAL ONLY; X=Xcad; Y=Ycad','plate_material':'G10 glass epoxy laminate, CNC, no metal backbone','plate_size_mm':[W,H,T],'window_xywh_mm':[20,20,220,30],'pad_centers_xy_mm':PADS,'nominal_pad_projection_mm':PROJECTION,'nominal_height_contact_to_marker_mm':HEIGHT,'height_excludes_optical_coating':True,'nominal_magnet_mm':[24,16,1.5],'nominal_magnet_stack_including_bond_protection_mm':1.6,'nominal_magnet_air_gap_mm':.1,'required_as_built_gap_range_mm':[.05,.15],'reference_temperature_C':20,'cte_x_per_K':None,'cte_y_per_K':None,'cte_status':'Measure batch-specific directional behavior; never reuse V1 316L coefficient.','dictionary':'DICT_4X4_50','marker_black_square_size_mm':12,'marker_border_bits':1,'quiet_zone_min_mm':2,'markers':tags,'features':features,'requirement':'Use serial-specific as-built XYZ measured under magnetic preload on validated steel fixture. Update height after pad rework. Same optical IDs as V1; operator must select correct serial/profile. Soft magnet is NOT the dimensional datum.'}
(OUT/'04_calibration/nominal_geometry.json').write_text(json.dumps(nominal,ensure_ascii=False,indent=2))
with (OUT/'04_calibration/as_built_measurement_template.csv').open('w',newline='',encoding='utf-8-sig') as f:
    wr=csv.writer(f);wr.writerow(['feature_id','nominal_x_mm','nominal_y_mm','nominal_z_mm','loaded_measured_x_mm','loaded_measured_y_mm','loaded_measured_z_mm','expanded_uncertainty_mm','temperature_C','frame_serial','steel_fixture','instrument','operator','date'])
    for p in features:wr.writerow([p['feature_id'],p['x_mm'],p['y_mm'],p['z_mm']]+['']*10)
    for i,(x,y) in enumerate(PADS):wr.writerow([f'CONTACT_P{i+1}',x,y,0]+['']*10)
with (OUT/'04_calibration/physical_acceptance_template.csv').open('w',newline='',encoding='utf-8-sig') as f:
    wr=csv.writer(f);wr.writerow(['test_id','required_result','measured_result','unit','frame_serial','steel_thickness_mm','paint_thickness_mm','temperature_C','orientation','instrument_uncertainty','operator','date','pass_fail'])
    for tid,goal,unit in [('PAD_SPREAD','<=0.01','mm'),('GAP_P1','0.05..0.15','mm'),('GAP_P2','0.05..0.15','mm'),('GAP_P3','0.05..0.15','mm'),('FREE_OPTICAL_FLATNESS','<=0.03','mm'),('LOADED_OPTICAL_FLATNESS','<=0.03','mm'),('REPEAT_XY_CHANGE_30_CYCLES','<=0.03','mm'),('REPEAT_Z_CHANGE_30_CYCLES','<=0.03','mm'),('NORMAL_HOLDING_FORCE','>=3*measured_weight_N','N'),('VERTICAL_SHEAR_HOLDING_FORCE','>=3*measured_weight_N','N'),('VERTICAL_DRIFT_60S','<=0.05','mm'),('SYSTEM_MAX_XY_ERROR_PLUS_U','<=0.20','mm')]:wr.writerow([tid,goal,'',unit]+['']*9)

def text(c,x,y,s,size=10,font='CJK'):c.setFont(font,size);c.drawString(x*mm,y*mm,s)
def line(c,x1,y1,x2,y2):c.line(x1*mm,y1*mm,x2*mm,y2*mm)
def box(c,x,y,w,h):c.rect(x*mm,y*mm,w*mm,h*mm,stroke=1,fill=0)
def circle(c,x,y,r):c.circle(x*mm,y*mm,r*mm,stroke=1,fill=0)
def title(c,s,n):
    box(c,10,10,400,277);text(c,18,275,s,16);text(c,18,264,'VIN-FRAME-V2-MAGNETIC / Rev A / 首件评审版：实体吸附及0.2毫米精度尚未验证',10)
    line(c,10,35,410,35);text(c,18,25,'单位mm；数值尺寸优先；正面左下角XY原点；STEP省略实际螺纹、涂层、螺钉。',9)
    text(c,18,17,'背面布局按正面XY透视定位，不是翻面后直接观察图；CAM翻面必须转换坐标。',9);text(c,350,20,f'A3 {n}/4',10,'Helvetica')
def view(c,x,y,pattern=False,back=False):
    c.roundRect(x*mm,y*mm,W*mm,H*mm,4*mm,stroke=1,fill=0)
    c.roundRect((x+20)*mm,(y+20)*mm,220*mm,30*mm,3*mm,stroke=1,fill=0)
    if pattern:
        for xx,yy,w,h in black:c.rect((x+xx)*mm,(y+yy)*mm,w*mm,h*mm,stroke=0,fill=1)
    if back:
        for i,(xx,yy) in enumerate(PADS):
            box(c,x+xx-12,y+yy-8,24,16);circle(c,x+xx,y+yy,5);circle(c,x+xx,y+yy,4.01);text(c,x+xx-6,y+yy+10,f'P{i+1}',8,'Helvetica')
def dim(c,x1,x2,y,base,label):
    line(c,x1,base,x1,y+2);line(c,x2,base,x2,y+2);line(c,x1,y,x2,y);text(c,(x1+x2)/2-16,y+3,label,9,'Helvetica')
c=canvas.Canvas(str(OUT/'01_drawings/manufacturing_drawings_A3.pdf'),pagesize=(420*mm,297*mm))
title(c,'01 玻纤环氧主体加工图：替代原316L金属框',1);view(c,65,170)
dim(c,65,325,248,240,'260 +/-0.10');dim(c,85,305,160,190,'220 +/-0.10')
text(c,335,210,'70 +/-0.10',9,'Helvetica');text(c,145,205,'窗口 220 x 30，原点(20,20)，R3',10)
for x,y in MOUNTS:circle(c,65+x,170+y,1.25)
for i,s in enumerate(['材料：有批次证明的G10玻纤环氧层压板；不覆铜，不用普通塑料/FDM/树脂打印。','厚度6.00±0.05；外角R4；接触边C0.2~0.3；毛坯建议约7~8厚，两面交替精修。','4×正面M3×0.5盲孔：(10,22)、(10,48)、(250,22)、(250,48)。','M3有效牙深2.5；从正面钻孔总深3.5，含钻尖；底孔与攻丝方法由工厂核定。','主体释放夹持后及磁吸载荷下，成像区平面度目标均≤0.03；达不到不得作为合格件。','孔位±0.05；STEP圆柱为简化底孔；不得全部通切；玻纤加工需专业吸尘与边缘封闭。','丝印/光刻前后均检查翘曲；强行压平加工、直接用原板厚度和普通PCB丝印不可作为验收。']):text(c,20,138-i*13,s,10)
c.showPage()
title(c,'02 背面三点磁贴与硬定位垫布局（按正面XY）',2);view(c,65,173,back=True)
for i,s in enumerate(['三组共用中心：P1=(14,11)，P2=(246,11)，P3=(130,60)。与V1接触点不同。','3×背面浅窝：Ø8.02 +0.02/0，深0.20±0.02；中心M2×0.4盲孔。','M2有效牙深2.5；从浅窝底钻孔总深3.4，含钻尖；禁止贯穿成像面。','3×磁贴：24×16×1.50，外角R1，中心贯通避让孔Ø10；裁切公差±0.20。','每片磁贴位于接触垫周围，使吸力靠近硬支点；强磁面朝车辆，背胶朝G10。','磁贴采购：优先柔性粘结钕铁硼；1.5厚仅为样件规格，须提供含胶厚度与间隙拉力数据。','磁片+粘接+保护层总厚名义1.60；不另加重复背胶；严禁磁片成为接触支撑面。','下料用magnetic_tile_cut_1to1.dxf；布局DXF只作定位，不能把参考轮廓全切。']):text(c,20,149-i*13,s,10)
c.showPage()
title(c,'03 定位垫与层叠剖面：磁吸固定不改变A基准',3)
# Local pad drawing magnified 8:1.
box(c,40,192,63.84,15.2);line(c,54.72,192,63.12,200.4);line(c,89.12,192,80.72,200.4)
line(c,63.12,200.4,63.12,207.2);line(c,80.72,200.4,80.72,207.2)
text(c,20,232,'PEEK垫剖面示意8:1；Ø7.98±0.01；厚1.90±0.01',11)
text(c,20,218,'通孔Ø2.2；90°沉头Ø4.3，深1.05；边缘轻倒钝。',10)
text(c,20,180,'3件配组：实际伸出量差≤0.01；M2×4沉头螺钉。',10)
text(c,20,167,'螺钉头径≤4.2，沉入接触面≥0.05；不得碰到车身。',10)
box(c,235,181,110,36);box(c,235,171.4,40,9);box(c,305,171.4,40,9)
box(c,235,180.4,40,.6);box(c,305,180.4,40,.6);box(c,285,170.8,10,11.4)
line(c,220,170.8,355,170.8)
text(c,230,232,'层叠名义值（局部示意，非比例）',11)
text(c,350,199,'G10 6.00',9,'Helvetica');text(c,350,176,'MAG 1.50',9,'Helvetica');text(c,230,158,'A：3片硬垫外侧面；磁片面高于A约0.10',10)
for i,s in enumerate(['名义：垫伸出=1.90-0.20=1.70；磁片堆栈=1.60；磁片离车面间隙=0.10。','必须实测：每处间隙均在0.05~0.15；按实际含胶/保护层厚度配磨三片垫，不强压软磁片。','修改垫厚后重新检查M2×4牙长、螺钉沉入量及基准高度，更新实测标定档案。','标记面距A名义7.70＋成像层厚度；不与钢印凸起等高，不得沿用V1的4.30高度。','普通磁片面保护膜、泡棉背胶或柔性防滑层不得进入三片硬垫的接触面。','可选手柄：V1外形兼容，装在G10正面Z=6；M3×5配0.5垫圈，有效咬合约1.5。','G10螺纹是低拆装次数结构；不规定未经验证的拧紧力矩，首件检查牙强度与松动。']):text(c,20,138-i*13,s,10)
c.showPage()
title(c,'04 正面光学图案与首件验收要求',4);view(c,65,175,pattern=True)
for i,s in enumerate(['图案沿用V1：14个12×12 ArUco，DICT_4X4_50，ID 0~13；10组3毫米棋盘格，共86特征点。','成像：白色哑光精密薄涂层＋黑色精密丝印/光刻；供应商评审，完成后逐框实测。','正式母版black_pattern_1to1.svg / black_pattern_filled.dxf；禁止镜像、描边、缩放。','必须在代表性钢板磁吸载荷下测量XYZ；扩展测量不确定度目标≤0.02，记录温度和框序列号。','30次吸附/取下：点坐标与高度变化各≤0.03；磁吸成像面平面度≤0.03。','最弱合格钢板/漆层：法向拉脱及竖直抗滑承载均≥成品重量力3倍；静置60秒滑移≤0.05。','系统验收：独立可溯源平面测试件，实际漆层/钢厚/姿态；关键点最大位置误差＋U≤0.20。','App须加载V2实测档案、畸变模型与新高度；输出PNG及毫米/像素元数据，未经实体验收不宣称合格。']):text(c,20,149-i*13,s,10)
c.save()

# Human-readable preview, never manufacturing artwork.
font_path='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font=ImageFont.truetype(font_path,25,index=2);smallfont=ImageFont.truetype(font_path,20,index=2)
preview=Image.new('RGB',(1500,1000),'white');p=ImageDraw.Draw(preview)
p.text((35,20),'VIN参考框 V2：G10硬质基准框 + 三点磁贴固定',font=font,fill='#16324c')
p.text((35,65),'中央窗口露出完整钢印；软磁片不承担尺寸与高度基准',font=smallfont,fill='#435461')
pattern=im.resize((1300,350)).convert('RGB');preview.paste(pattern,(100,125))
p.rounded_rectangle((100,125,1400,475),radius=20,outline='#4f7250',width=3)
p.rounded_rectangle((200,225,1300,375),radius=15,fill='#e9edf0',outline='#748795',width=2)
p.text((455,280),'车辆识别代号 / 中央开窗 220×30 mm',font=font,fill='#223c51')
p.text((35,500),'背面布局（沿用正面XY透视，不镜像）：磁贴环绕硬接触垫',font=smallfont,fill='#223c51')
p.rounded_rectangle((100,560,1400,910),radius=20,fill='#d5e0c4',outline='#4f7250',width=3)
p.rounded_rectangle((200,660,1300,810),radius=15,fill='white',outline='#748795',width=2)
for i,(x,y) in enumerate(PADS):
    xx,yy=100+x*5,910-y*5
    p.rounded_rectangle((xx-60,yy-40,xx+60,yy+40),radius=5,fill='#323638')
    p.ellipse((xx-25,yy-25,xx+25,yy+25),fill='#d5e0c4')
    p.ellipse((xx-20,yy-20,xx+20,yy+20),fill='#c6ad7b')
    p.text((xx-20,yy+42),f'P{i+1}',font=smallfont,fill='#223c51')
p.text((35,950),'示意图不表达公差。样件须验证吸力、防滑、加载形变及整机≤0.2 mm误差。',font=smallfont,fill='#435461')
preview.save(OUT/'01_drawings/magnetic_design_preview.png')

# Digital checks: true solid geometry, contacts, optical recognition and nominal gaps.
dp=cv2.aruco.DetectorParameters();dp.cornerRefinementMethod=cv2.aruco.CORNER_REFINE_SUBPIX
corners,ids,_=cv2.aruco.ArucoDetector(DICT,dp).detectMarkers(np.array(im.resize((2600,700))))
assert ids is not None and set(ids.ravel())==set(range(14))
assert len(features)==86
for x,y,w,h in black:
    assert not (x<240 and x+w>20 and y<50 and y+h>20)
    for xx,yy in MOUNTS:assert not (x<xx+5 and x+w>xx-5 and y<yy+4 and y+h>yy-4)
for x,y in PADS:
    placed=mag.translate((x,y,-MAG_T-BOND_T))
    assert abs(placed.val().BoundingBox().zmin+1.6)<1e-6
    assert body.intersect(placed).val().Volume()<1e-6 if body.intersect(placed).vals() else True
    placed_pad=pad.translate((x,y,-PROJECTION))
    overlap=placed_pad.intersect(placed)
    assert not overlap.vals() or sum(v.Volume() for v in overlap.vals())<1e-6
    # Magnetic projected footprint must lie entirely within frame (the pad hole is intentional).
    projected=mag.translate((x,y,0))
    assert abs(projected.intersect(body).val().Volume()-mag.val().Volume())<1e-6
assert abs(PROJECTION-(MAG_T+BOND_T)-.1)<1e-9
mag_area=mag.val().Volume()/MAG_T
checks={'status':'DIGITAL_CHECKS_PASSED_PHYSICAL_PROTOTYPE_NOT_TESTED','body_bbox_mm':[body.val().BoundingBox().xlen,body.val().BoundingBox().ylen,body.val().BoundingBox().zlen],'body_volume_mm3':body.val().Volume(),'estimated_body_mass_g_at_density_1_82':body.val().Volume()*.00182,'magnetic_area_total_cm2':mag_area*3/100,'ideal_contact_force_N_using_450_g_per_cm2_NOT_actual':mag_area*3/100*.450*9.81,'nominal_gap_mm':.1,'nominal_height_mm':HEIGHT,'aruco_detected_ids':sorted(map(int,ids.ravel())),'feature_count':len(features),'solid_validity':{n:o.val().isValid() for n,o in models.items()},'magnetic_tiles_inside_frame':True,'magnet_pad_no_interference':True,'limitations':['No physical sample manufactured or measured','No measured adhesion/shear strength or loaded distortion','No camera calibration or 0.2 mm system certification','No supplier process validation','Nominal bond thickness is a schematic; self-adhesive sheet thickness must be measured']}
(OUT/'digital_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
manual=(ROOT/'manual.md').read_text()
(OUT/'制作与验收说明.md').write_text(manual)
styles={'body':ParagraphStyle('body',fontName='CJK',fontSize=9.2,leading=14,spaceAfter=6,wordWrap='CJK'),'title':ParagraphStyle('title',fontName='CJK',fontSize=16,leading=22,spaceAfter=12),'head':ParagraphStyle('head',fontName='CJK',fontSize=12,leading=18,spaceBefore=10,spaceAfter=6,wordWrap='CJK')}
story=[]
for para in manual.split('\n\n'):
    para=para.strip()
    if not para:continue
    style='body'
    if para.startswith('# '):para=para[2:];style='title'
    elif para.startswith('## '):para=para[3:];style='head'
    story.append(Paragraph(escape(para).replace('\n','<br/>'),styles[style]))
SimpleDocTemplate(str(OUT/'制作与验收说明.pdf'),pagesize=(210*mm,297*mm),leftMargin=18*mm,rightMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm).build(story)
(OUT/'README.md').write_text('''# VIN参考框 V2 磁吸版\n\n采用6毫米G10玻纤环氧主体、三片柔性钕铁硼磁贴及三点PEEK硬定位垫，取消金属骨架。中央开窗露出钢印。\n\n先读《制作与验收说明》，再看4页A3加工图。此版本是首件加工评审包，未通过实体吸力、磁吸形变或系统0.2毫米验收。不可把软磁片直接作为尺寸基准。\n\n- `01_drawings/`：加工PDF和结构预览。\n- `02_cad/`：主体、垫、磁贴及名义胶层STEP；装配STEP；主体/磁贴下料DXF；背面定位DXF。\n- `03_artwork/`：毫米尺寸SVG、填充DXF、1:1 PDF、位图。\n- `04_calibration/`：设计坐标、磁吸状态实测模板、实体验收模板。\n- `05_printed_handles/`：可选ASA/PETG辅助手柄STEP/STL。\n- `06_sources/`：可再生成文件的脚本、说明原文、依赖和嵌入字体。\n\n设计XY及图案保持V1外形；接触点、材料、热模型及标记面高度已更改。严禁直接沿用V1校准档案。\n\n复现：在06_sources中安装requirements.txt，运行 `python build_package.py`；如修改中文文本，先运行 `python embed_font.py`（需要系统Noto Sans CJK字体）。\n''')
requirements='cadquery==2.7.0\nez­dxf==1.4.4\nopencv-contrib-python-headless==4.11.0.86\nnumpy==2.3.5\nPillow>=10\nreportlab>=4\nfonttools>=4\n'.replace('ez­dxf','ezdxf')
(OUT/'06_sources/requirements.txt').write_text(requirements)
for name in ['build_package.py','manual.md','embed_font.py','cjk_embed.ttf','font_license.txt']:shutil.copy2(ROOT/name,OUT/'06_sources'/name)
paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT).as_posix()}\n' for p in paths))
with zipfile.ZipFile(ROOT/'VIN_FRAME_V2_MAGNETIC_manufacturing_package.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(ROOT))
print(json.dumps(checks,ensure_ascii=False,indent=2))
print('Complete package files:',len(paths)+1)
