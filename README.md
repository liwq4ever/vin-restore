# 车架号等尺寸拍摄：磁吸参考框制作包

本仓库提供普通手机、专用App及磁吸参考框的制作资料。目标为平面钢印区域约200毫米范围内，校正照片的关键点最大二维位置偏差不超过0.2毫米。

**当前为Rev B首件设计，已检查数字文件，尚未进行实体加工、吸附/防滑测试和0.2毫米整机验收。设计坐标不能代替成品实测校准。**

## 下载与阅读

- [完整制作包ZIP](downloads/VIN_FRAME_V2_MAGNETIC_manufacturing_package.zip)：29项文件，包含STEP、DXF、光学母版、加工图、制作说明及实测/验收模板。
- [四页A3加工图PDF](manufacturing/VIN_FRAME_V2_MAGNETIC/01_drawings/manufacturing_drawings_A3.pdf)。
- [制作与验收说明PDF](manufacturing/VIN_FRAME_V2_MAGNETIC/制作与验收说明.pdf)。
- [可直接浏览的制作说明](manufacturing/VIN_FRAME_V2_MAGNETIC/制作与验收说明.md)。
- [文件索引](manufacturing/VIN_FRAME_V2_MAGNETIC/README.md)。

下载ZIP时打开文件页面后选择 **Raw / Download raw file**；也可在仓库 **Code → Download ZIP** 下载整个仓库。

## 磁吸结构

主体采用CNC加工的G10玻纤环氧板，尺寸260×70×6毫米，中央开窗220×30毫米。三片柔性粘结钕铁硼磁贴围绕三片PEEK硬定位垫，吸附在钢印周围的平整钢面，窗口露出完整钢印。

磁贴负责固定，硬质主体保持图案尺寸，硬定位垫定义车身接触基准。磁贴不接触承重，名义空气间隙0.10毫米；标记面距接触基准名义7.70毫米加成像涂层，正式使用必须加载逐框实测XYZ和实际高度。主体估算约127克，不含磁贴、定位垫及紧固件。

正面采用14个ArUco和30个棋盘内部角点，共86个特征点。App必须使用对应手机标定及磁吸参考框序列号档案，补偿畸变和参考面高度差。仅提交电子照片时，输出固定毫米/像素的PNG及明确物理范围的JSON。

纯软磁片直接印图案不作为该精度目标的正式方案。此设计适用于实际试验确认可磁吸的平面钢制区域；铝制或吸力不足部位不在使用范围内。

![磁吸参考框结构示意](manufacturing/VIN_FRAME_V2_MAGNETIC/01_drawings/magnetic_design_preview.png)

## 文件目录

| 目录 | 内容 |
|---|---|
| `01_drawings/` | 四页加工图和结构预览 |
| `02_cad/` | G10主体、PEEK垫、磁贴、名义胶层、装配STEP和加工/裁切DXF |
| `03_artwork/` | 毫米尺寸SVG、填充DXF、1:1 PDF和位图 |
| `04_calibration/` | 名义坐标JSON、磁吸状态实测CSV、实体验收CSV |
| `06_sources/` | 生成脚本、说明原文、依赖及嵌入字体许可 |
| `downloads/` | 完整制作包ZIP |

制造目录位于 `manufacturing/VIN_FRAME_V2_MAGNETIC/`。

## 加工与验证

先让加工厂评审PDF和STEP，再做1～3件样件。主体背面仅加工三组定位垫浅窝和M2盲孔，实际螺纹与深度以PDF为准；粗切只用轮廓DXF，禁止把盲孔图层一起切穿。成像使用独立黑色图案母版，不使用带尺寸和文字的加工图。

完成装配后，在代表性钢板磁吸载荷下测量序列号对应的光学点XYZ、接触基准、高度、平面度及温度，填写实测表。验证实际钢板/漆层上的法向拉脱、竖直抗滑、重复吸附几何稳定性和温湿影响。

最终用未参与标定的独立测试件验收整套系统，要求关键点最大位置误差加测量扩展不确定度不超过0.20毫米。名义JSON、合成图识别和CAD有效性均不能证明实物达到此精度。

文件完整性清单：[SHA256SUMS.txt](manufacturing/VIN_FRAME_V2_MAGNETIC/SHA256SUMS.txt)；数字检查记录：[digital_checks.json](manufacturing/VIN_FRAME_V2_MAGNETIC/digital_checks.json)。
