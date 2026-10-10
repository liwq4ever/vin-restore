# VIN参考框 V2 磁吸版

采用6毫米G10玻纤环氧主体、三片柔性钕铁硼磁贴及三点PEEK硬定位垫，取消金属骨架。中央开窗露出钢印。

先读《制作与验收说明》，再看4页A3加工图。此版本是首件加工评审包，未通过实体吸力、磁吸形变或系统0.2毫米验收。不可把软磁片直接作为尺寸基准。

- `01_drawings/`：加工PDF和结构预览。
- `02_cad/`：主体、垫、磁贴及名义胶层STEP；装配STEP；主体/磁贴下料DXF；背面定位DXF。
- `03_artwork/`：毫米尺寸SVG、填充DXF、1:1 PDF、位图。
- `04_calibration/`：设计坐标、磁吸状态实测模板、实体验收模板。
- `05_printed_handles/`：可选ASA/PETG辅助手柄STEP/STL。
- `06_sources/`：可再生成文件的脚本、说明原文、依赖和嵌入字体。

设计XY及图案保持V1外形；接触点、材料、热模型及标记面高度已更改。严禁直接沿用V1校准档案。

复现：在06_sources中安装requirements.txt，运行 `python build_package.py`；如修改中文文本，先运行 `python embed_font.py`（需要系统Noto Sans CJK字体）。
