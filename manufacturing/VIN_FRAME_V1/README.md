# VIN_FRAME_V1 首件制作包

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
