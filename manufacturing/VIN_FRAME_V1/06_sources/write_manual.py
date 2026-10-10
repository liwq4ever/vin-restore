from pathlib import Path
import json, shutil, hashlib, zipfile
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'VIN_FRAME_V1'
if (ROOT/'cjk_embed.ttf').exists():
    pdfmetrics.registerFont(TTFont('STSong-Light',str(ROOT/'cjk_embed.ttf')))
else:
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

MANUAL='''# VIN参考框V1：制作、测量与使用说明

版本：Rev A；日期：2026-10-10。此包是可供加工厂评审和首件打样的设计文件，不是已通过0.2毫米验收的产品图纸。适用于单位统一手机、专用App、平面钢印区域和仅提交电子照片的项目。

## 1. 设计边界及结构

目标是使钢印周围金属基准面上的二维照片尺寸准确；不测量或恢复字符凹槽的三维表面。参考框标记面不必与字符笔画等高：软件通过已测得的高度和相机姿态，将图像映射到车身接触基准面。

首版适配假设：钢印区域约200×20毫米以内；开窗220×30毫米；安装空间约260×70毫米，手柄安装后横向约290毫米。先在代表性车辆上检查空间及三个接触点，不适配就修改尺寸并重新生成/测量，不能缩放现有图纸凑尺寸。

金属框260×70×3毫米，外角R4，开窗位于X=20~240、Y=20~50，内角R3。金属框约278克，不含垫片和手柄。参考框背面三个PEEK接触垫定义接触基准A。A应与钢印周围金属基准面重合；中间钢印区域是否平整，仍须现场验证。

接触垫中心（正面XY）：P1=(10,10)，P2=(250,10)，P3=(130,60)。PEEK垫厚1.50，插入0.20深的浅窝，伸出金属底面约1.30。标记面距离A约3.00+1.50-0.20=4.30毫米，再加成像层厚度。这个4.30只是设计值，正式使用时替换为成品实测值。

金属框平面度、三点定位和中间钢印表面起伏都影响精度。三点接触能定义支撑平面，不能自动证明中央钢印与它共面。不得用海绵、橡胶、软胶或3D打印面替代接触基准。

## 2. 材料选择

金属框：首版推荐316L不锈钢（EN 1.4404），CNC加工后稳定精修。它耐用且有成熟加工供应链，但并非零热膨胀材料。可选Invar 36低膨胀合金用于大温差方案；换材后须重新审查加工、表面防护、热膨胀数据和标定，不能直接沿用316L数据。

接触垫：本色、未填充PEEK棒料CNC车削。使用未填充材料以减少硬填料擦伤风险。低成本识别样件可以用POM-C，但不能未经测量和温区/重复定位验证就宣布与PEEK等效。

手柄：3D打印ASA用于户外辅助握持，PETG可用于室内打样。仅是辅助件；不承担图形尺度、支撑高度或接触面。金属框、PEEK接触垫和正式黑白图案不采用普通FDM/树脂打印作为计量基准。

成像层：白色哑光薄涂层，加黑色精密成像。建议供应商先试验高精度丝印/光刻油墨方案；普通UV打印是否可用由成品边缘和尺寸实测决定，不能用宣传dpi替代计量验收。

## 3. 文件使用顺序

先读本说明和01_drawings/manufacturing_drawings_A3.pdf，再看02_cad/assembly_nominal.step。金属厂使用metal_frame.step配合四页PDF；STEP的螺纹孔为简化底孔，不包含真实螺纹、钻尖、倒角或涂层。

rough_cut_profile_only.dxf只有外形和窗口轮廓，适合粗切。metal_frame_operations.dxf按图层表示外形、开窗、背面浅窝、背面M2底孔、正面M3底孔；禁止把所有图层当成通孔激光切割。盲孔深度和螺纹以PDF数值为准。

成像厂使用03_artwork/black_pattern_1to1.svg或black_pattern_filled.dxf。SVG声明物理尺寸260×70毫米。DXF为毫米，BLACK_FILLED_AREAS是填满的黑色面积，不是只雕轮廓。图案不镜像、不旋转、不更改ID、不描边。DXF使用HATCH填充，导入设备后先确认填充仍有效。

black_pattern_1to1.pdf页面为280×90毫米，图案在页面内距四周10毫米。它不是A4页面，打印时用实际大小，不适合页面。pattern_1524ppi.png是便于检查/打样的位图，原尺寸15600×4200像素；正式制作优先用矢量母版。不要把带文字的加工图或pattern_overview.png拿去制作标记。

nominal_geometry.json是开发用设计坐标，明确标记NOMINAL_ONLY_NOT_VALID_FOR_PRODUCTION。它不是校准证书。as_built_measurement_template.csv的实测栏为空，必须由实物测量填写。

## 4. 金属框加工流程

步骤1：供应商评审。确认316L材料、薄框加工夹持、成品平面度、浅盲孔攻丝和后续成像能力；确认安装空间。先做1~3件样件，不先批量生产。

步骤2：下料。采用有材质证明且状态稳定的板材，建议从约4毫米厚的余量毛坯起做。毛坯外形建议留加工余量。若激光/水切粗切，轮廓留约0.2~0.5毫米精加工余量，具体由工厂确定；粗切文件本身是名义成品轮廓，粗切余量由CAM增加。

步骤3：粗加工两面和窗口。交替加工两面，留精加工余量，避免强行压平后一次铣成品。粗加工后释放夹持、稳定并检查回弹。材料稳定/去应力工艺由供应商针对316L制定，不在这里规定未经验证的热处理配方。

步骤4：精修。成品厚3.00±0.05，外形和窗口±0.10；外角R4、内角R3。机械图形边缘不作为尺寸标尺，因此外形公差无需做到光学特征点的测量等级。用精铣/磨削或合适的稳定工艺达到平面度目标；必须在释放夹持后测量。

步骤5：背面三组浅窝与盲孔。浅窝Ø8.02 +0.02/0，深0.20±0.02；中央M2×0.4，有效牙深1.5，从浅窝底钻孔总深2.2（含钻尖）。底孔直径/攻丝方法由加工厂核定。禁止贯穿正面。

步骤6：正面手柄孔。4×M3×0.5，孔位(10,22)、(10,48)、(250,22)、(250,48)，有效牙深1.5，钻孔总深2.5（含钻尖）。不装手柄也可保留。应核对实用钻尖角、攻丝底部空间和剩余壁厚；如工厂无法可靠加工，先评审修改图纸，不能擅自打通。

步骤7：去毛刺和清洁。外缘与窗口触及边倒钝约C0.2~0.3，角部圆滑；避免刃口划伤车辆。采用供应商认可的表面清洁/防护工艺。将三处浅窝底、定位配合和螺纹区遮蔽，避免成像涂层进入接触装配基准。

步骤8：记录机械首检。检查尺寸、释放夹持后的平面度、盲孔实际深度、螺纹和浅窝深度。上表面完成成像后的光学区域平面度目标≤0.03毫米；若达不到，须重新评估误差预算或用经验证的三维参考点模型，不能按理想平面使用。

## 5. PEEK接触垫制作与装配

车削三片PEEK垫：外径7.98±0.01，厚1.50±0.01；通孔Ø2.20；接触侧90°沉头Ø4.30，理论深1.05。接触面平整、无毛刺，外缘轻微倒钝≤0.05；三片配组厚度差≤0.01。接触垫是CNC件，不能直接用打印垫替代。

用M2×3、90°沉头螺钉固定，实际头径≤4.20。螺钉头必须低于PEEK接触面至少0.05，避免金属头碰车身。真实螺钉长度从沉头顶端计；装配前核对头部尺寸、嵌入深度及盲孔，不可顶底。CAD不含螺钉。

PEEK垫的背面必须靠实浅窝底，以硬接触确定高度；不加胶或软垫。低预紧固定，避免把薄垫压变形；预紧力由样件试验确定。检查松动和反复装配后的高度变化。若垫片磨损、拆换或螺钉调整，重新测量该框。

将装好垫片的金属框放在洁净、已检定的平面基准上，确认三点稳定接触、没有其他部位接触。接触面不得带砂粒和异物，允许与车辆接触的方式由现场工艺确认。

## 6. 黑白图案制作流程

步骤1：先在同材料试片上试验。确认白色底层哑光、均匀、耐擦拭；黑层高对比、附着可靠，照明下无明显镜面高光。丝印、UV或光刻的候选工艺都以成品测量为判断依据。

步骤2：正面白色薄层。湿式薄涂层可先以约20~40微米为打样起点，黑层约5~15微米作为工艺探索范围；这些不是供应商已保证的公差。总厚度、厚度均匀性、固化温度和耐清洁性须实测。不要用厚塑封、普通覆膜或未经控制的胶层覆盖正式图案。

步骤3：制作成像母版。按SVG/DXF做菲林或光绘，不改变物理尺寸。摄像头视角下ID0~5在上边(Y=60)，ID6~11在下边(Y=10)，ID12在左，ID13在右。表面上不印图纸说明和尺寸线。

步骤4：精密成像。图案定位/尺寸目标±0.05；每个棋盘交点附近的线边毛糙、弯曲或溢墨目标≤0.03。该指标需要显微检查，不是要求普通打印机自动达到它。白色隔离区至少2毫米，不允许黑污、编号或紧固件侵入。

步骤5：固化后检查。再次测平面度，确认14个编码方向和ID正确、30个棋盘内部角点完整、图案与窗口/手柄无冲突。图形耐清洁工艺先在试片测试，避免未经验证的溶剂损伤油墨。

步骤6：侧面编号。唯一序列号写在侧面或非光学区域。每个框有独立实测数据；不通过改变编码字典ID来随意区分各框，以免软件布局失配。App可手动选框，或后续另设不侵入隔离区的序列号读码位置并验证。

## 7. 精密图案及软件对应关系

编码：OpenCV DICT_4X4_50，ID0~13，1格黑边。外黑方框12×12毫米，内部4×4数据加四周1格边框形成6×6格，每格2毫米；每边外至少留2毫米白色。

棋盘条：10组4列×2行，单格3毫米，每组图形12×6毫米。中心为X=50,90,130,170,210，Y=10与60；每组3个内部交点，共30个。编码用于定位和消除方向歧义；棋盘内部角点用于精细定位，其他特征按实测不确定度加权。它是定制ArUco＋棋盘布局，不是可直接套用完整ChArUcoBoard的板。

56个编码角点加30个棋盘角点共86点。编码角点顺序按OpenCV输出：TL、TR、BR、BL，摄像头看到的上方对应较大的Y。CAD原点在金属底面；开发JSON的Z=0是接触A面，名义换算Zjson=Zcad+1.30。正式标定时改用实测坐标变换。

算法须使用标定相机求姿态并映射到钢印A平面。对标记面直接做单应性校正后输出会恢复标记面，而不是下面的钢印面。相机内参/距离估计误差也会影响高度补偿；4.30毫米高差是否可以满足整机0.2毫米必须通过独立测试确认。

开发示例JSON故意保留“未校准”状态。生产App应拒绝用它生成精度合格结果，不得把CAD坐标复制到实测栏完成校准。序列号必须与实物一致。

## 8. 成品测量与校准流程

委托具备影像测量和测高能力的计量/精密加工单位。推荐关键光学点XY扩展测量不确定度U(k=2)≤0.02毫米，目标可进一步收紧到0.01；高度/点Z的不确定度建议≤0.02。确认仪器实际能力及其报告，不能只看仪器显示分辨率。

测量前在约20±1摄氏度环境充分均温，记录框的实际温度和参考温度。完成涂层、垫片、螺钉和计划使用的手柄后再测量。让三个接触垫在合格平面基准上以规定轻载稳定接触，由这一实际支撑平面建立A；不能只拟合三个垫片中心就忽略垫面倾斜和螺钉突出。

测量实际光学角点的XYZ。XY坐标原点可由外轮廓直边形成虚拟左下角，并投影到A；对算法而言关键是所有特征点与A之间采用一致且有记录的坐标关系。Z应相对于A，包含基体厚度、浅窝深度、垫片厚度和成像层。

逐点填写04_calibration/as_built_measurement_template.csv。列出测量温度、序列号、仪器、人员、日期及不确定度。若供应商输出其他坐标系，必须提供可复核的坐标变换和基准定义。

测量A到光学参考面的高度h和参考面相对A的倾斜；检查整个光学区域平面度。若点位非平面但三维坐标测量可靠，可由研发评估使用3D特征点PnP；不可在平面模型中忽略超差起伏。

重复取放、改变轻载及装卸手柄，检查h和图形位置变化。只做一次静态测量不能证明现场重复性。拿独立测试件验证校准，而不是再用参与拟合的参考点证明自身准确。

## 9. 温度与机械载荷

316L资料表的20~100摄氏度平均线膨胀系数约16×10^-6/K。200毫米长度变化20摄氏度约0.064毫米；260毫米参考基线变化20摄氏度约0.083毫米。这已占用0.2毫米预算的一部分，必须控制或补偿。

首轮精度验证可以限制框温在标定温度±3摄氏度。实际室外使用时测量框温，按经验证的系数进行X、Y尺度修正，比例约1+α(T-T0)；温度计测的是金属框温度，而不是仅记录天气或手机温度。系数来自材料表时仍是近似值，需在实际温区验证；不要把20~100摄氏度平均系数未经验证地外推到所有温度。JSON中的16e-6不是单件热膨胀证书。

三点定位避免四脚摇晃，但施力点若在支撑三角形外，框仍可能翘起。手柄用于拿取，不能用单侧手柄大力下压。拍摄时要保证三个接触点稳定、载荷与标定/验证条件一致。

竖直或仰拍部位需要非基准的辅助固定方式，如现场认可的夹具；固定力尽量靠近接触点，不能把金属框夹弯。具体车身固定夹具未包含在本包，需现场样件确认。增加固定方式后也须验证重复性，不可用未知厚度软胶来承载A面。

## 10. 可选3D打印手柄

05_printed_handles/handle.stl打印2件；一件用于左侧，另一件旋转180度用于右侧。另附STEP和06_sources/frame_parametric.scad。STL单位无强制标准，本包按毫米；切片后外包络应约30×34×15毫米，先核对尺寸。

层高建议0.20毫米，4道外壁，约35%填充；温度、风扇和热床按耗材厂商参数。安装面朝打印平台可减少支撑。ASA需合适设备/环境，PETG便于室内试装。打印孔可轻修到Ø3.4，安装面实际厚度须测量。

用4颗M3×5螺钉和4片0.5毫米厚垫圈安装，名义牙进入金属约1.5；必须以真实零件尺寸核对，不得顶盲孔底。不强行拧紧打印件消除翘曲。两臂位于Y=18~26和44~52，避开侧面编码及白色隔离区。

打印件不应低于金属框底面，装配后与车身建议至少0.8毫米净间隙。它不能接触车身形成第四个支撑点，也不能压迫或遮挡图案。装手柄后重新检查机械与光学状态。

## 11. 首件与系统验收

第一层：机械检查。确认几何、盲孔、毛刺、PEEK接触状态、螺钉头退让、成像后平面度和三点稳定性。第二层：光学检查。实物拍摄应识别14个ID，角点可稳定定位，反光与毛边受控；图案设计文件已通过数字识别检查，但这不能替代实物检查。

第三层：成品计量。得到序列号对应的实测XYZ、A面、高度、温度与不确定度。第四层：独立整机验收。用未参与标定的精密刻线/模拟钢印测试件，测试首端、中间、末端及上下位置，并重复取放、多人操作、改变允许角度、距离、光照和温度。

目标：允许整体平移和旋转后，预定义关键点的最大二维位置偏差，加相应测量不确定度，不超过0.2毫米。不允许额外缩放或局部变形。测试本地PNG和业务系统下载PNG，确认像素/毫米及文件完整性均保持。

现场钢印表面起伏必须单独调查。200毫米范围、约250毫米拍摄距离下，未知高度误差0.10毫米可贡献约0.08毫米尺度误差；因此把残余高度不确定性压到约0.05毫米量级是研发目标，不是本图纸可自动保证的车辆条件。

日常：使用独立校验件开工检查；发现标记损坏、接触垫磨损、框变形、螺钉松动时停用该框，处理后重新验证。手机、拍照模式、系统或App版本变化时按项目流程核验标定。

## 12. 首件采购清单及交付要求

每套：316L金属框1件；CNC PEEK接触垫3件；M2×3沉头螺钉3颗；精密白底黑色成像1套；可选打印手柄2件，M3×5螺钉4颗及0.5毫米垫圈4片；独立序列号及成品测量报告1份。

供应商交付：材质信息、机械首检记录、成像工艺与耐清洁验证、成品平面度、每点XYZ及测量不确定度、参考温度、装配高度、照片和序列号。报价应分机械加工、图形成像、计量测量、辅件和报告五项；精密测量可能比原材料更决定成本。

数字文件核验记录见digital_checks.json。已核验CAD实体有效性、外包络、图案隔离、开窗避让及14个编码的合成图识别。尚未进行实体加工、实际手机拍摄和0.2毫米精度试验。因此此版本用于首件评审和验证，不代表正式产品认证。

## 13. 资料依据

OpenCV官方ArUco检测说明（编码结构、角点精细定位）：https://docs.opencv.org/4.11.0/d5/dae/tutorial_aruco_detection.html

Outokumpu Supra不锈钢材料表（316L密度、热膨胀系数等）：https://www.outokumpu.com/en/products/product-ranges/-/media/files/products/supra/outokumpu-supra-range-datasheet.pdf?modified=20251117111951&revision=7a909396-d1f3-4d36-9c1c-99606be41fd2

Victrex PEEK材料说明（尺寸稳定性及蠕变特性）：https://www.victrex.com/en/products/polymers/peek-polymers

Prusa ASA材料说明（户外辅助打印件）：https://help.prusa3d.com/article/asa_1809

本包的尺寸、公差和工艺窗口属于项目首版工程设计，资料来源不构成对本参考框的精度保证。
'''
(OUT/'制作与验收说明.md').write_text(MANUAL,encoding='utf-8')

README='''# VIN_FRAME_V1 首件制作包

先阅读《制作与验收说明》PDF和Markdown，再交给加工厂评审。

本包是Rev A样件设计，数字文件经过检查；尚无实物、手机或0.2毫米精度验收结果。

| 文件 | 用途 |
|---|---|
| 01_drawings/manufacturing_drawings_A3.pdf | 4页机械、垫片、装配、图案加工图 |
| 02_cad/metal_frame.step | CNC金属框，螺纹孔简化为底孔 |
| 02_cad/peek_contact_pad.step | CNC PEEK接触垫，需3件 |
| 02_cad/assembly_nominal.step | 金属框、3垫片、2可选手柄的名义装配 |
| 02_cad/rough_cut_profile_only.dxf | 仅轮廓粗切，CAM自行留余量 |
| 02_cad/metal_frame_operations.dxf | 分层定位背面浅窝和盲孔，禁止全部切穿 |
| 03_artwork/black_pattern_1to1.svg | 1:1黑色实心图形母版，无文字、标注 |
| 03_artwork/black_pattern_filled.dxf | 图案DXF，黑色区域为HATCH填充 |
| 03_artwork/black_pattern_1to1.pdf | 280×90毫米页面的1:1图案 |
| 03_artwork/pattern_1524ppi.png | 15600×4200像素，1524ppi，便利打样文件 |
| 04_calibration/nominal_geometry.json | 设计坐标，未校准，禁止生产直接使用 |
| 04_calibration/as_built_measurement_template.csv | 成品测量表，实测栏留空 |
| 05_printed_handles/handle.stl | ASA/PETG可选辅助手柄，打印2件 |
| 05_printed_handles/handle.step | 可编辑手柄三维文件 |
| 06_sources/frame_parametric.scad | OpenSCAD源文件，可选择body/pad/handle/assembly |
| 06_sources/build_package.py | 本包生成脚本，含CAD、图案和数字检查 |
| digital_checks.json | 数字校验结果，不是物理精度证明 |
| SHA256SUMS.txt | 文件完整性清单 |

零件尺寸单位都是毫米；STL必须在切片时确认单位。图纸深度和螺纹优先于简化STEP。

推荐正式框316L CNC加工、PEEK垫CNC加工、精密白底黑图成像。3D打印仅用于可选手柄。

参考高度约4.30毫米加成像层，必须实测。工作温度变化、实际钢印平面度和夹持重复性要独立验证。

更改外形、窗口、图案或材质后需更新相应文件、重新测量和验收。不要整套缩放文件。
'''
(OUT/'README.md').write_text(README,encoding='utf-8')

# Render the complete Chinese manual to a paginated, selectable-text PDF.
base=ParagraphStyle('base',fontName='STSong-Light',fontSize=10,leading=15.5,wordWrap='CJK',spaceAfter=5,textColor=colors.HexColor('#243746'))
h1=ParagraphStyle('h1',parent=base,fontSize=19,leading=27,spaceAfter=16)
h2=ParagraphStyle('h2',parent=base,fontSize=13,leading=20,spaceBefore=10,spaceAfter=8,keepWithNext=True,textColor=colors.HexColor('#12536c'))
def footer(c,doc):
    c.setFont('STSong-Light',8);c.setFillColor(colors.HexColor('#607482'))
    c.drawString(18*mm,13*mm,'VIN-FRAME-V1 / Rev A / 首件评审与验证用 / 实测前不得作为已校准参考框')
    c.drawRightString(192*mm,13*mm,str(doc.page))

story=[]
for block in MANUAL.strip().split('\n\n'):
    if block.startswith('# '):
        story.append(Paragraph(escape(block[2:]),h1))
        story.append(Image(str(OUT/'01_drawings/assembly_preview.png'),width=174*mm,height=87*mm))
        story.append(Spacer(1,8*mm))
    elif block.startswith('## '): story.append(Paragraph(escape(block[3:]),h2))
    else:
        # URL paragraphs are reduced to avoid long unbreakable strings.
        if 'https://' in block:
            label,url=block.split('https://',1)
            story.append(Paragraph(escape(label)+f'<link href="https://{escape(url)}" color="#12536c">打开官方资料</link>',base))
        else: story.append(Paragraph(escape(block).replace('\n','<br/>'),base))
SimpleDocTemplate(str(OUT/'制作与验收说明.pdf'),pagesize=(210*mm,297*mm),leftMargin=18*mm,rightMargin=18*mm,topMargin=18*mm,bottomMargin=22*mm,title='VIN参考框V1：制作、测量与验收说明',author='Engineering prototype').build(story,onFirstPage=footer,onLaterPages=footer)

shutil.copy2(ROOT/'build_package.py',OUT/'06_sources/build_package.py')
shutil.copy2(ROOT/'write_manual.py',OUT/'06_sources/write_manual.py')
if (ROOT/'cjk_embed.ttf').exists():
    shutil.copy2(ROOT/'cjk_embed.ttf',OUT/'06_sources/cjk_embed.ttf')
    shutil.copy2(ROOT/'embed_font.py',OUT/'06_sources/embed_font.py')
    license_file=Path('/usr/share/doc/fonts-noto-cjk/copyright')
    if license_file.exists(): shutil.copy2(license_file,OUT/'06_sources/font_license.txt')
(OUT/'06_sources/requirements.txt').write_text('cadquery==2.7.0\nopencv-contrib-python-headless==4.11.0.86\nezdxf==1.4.4\nreportlab>=4.0\nPillow>=10\nnumpy>=2.0\n',encoding='utf-8')

sha=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name!='SHA256SUMS.txt': sha.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(OUT).as_posix())
(OUT/'SHA256SUMS.txt').write_text('\n'.join(sha)+'\n',encoding='utf-8')
z=ROOT/'VIN_FRAME_V1_manufacturing_package.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED) as f:
    for p in sorted(OUT.rglob('*')):
        if p.is_file(): f.write(p,p.relative_to(ROOT))
print('Package:',z)
print('Files:',len(sha)+1,'ZIP bytes:',z.stat().st_size)
