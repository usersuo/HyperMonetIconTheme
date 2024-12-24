import re
import xml.etree.ElementTree as ET

from pathlib import Path


class MappingProcessor:
    """图标映射处理器

    用于处理图标映射关系: 
    1. 解析appfilter.xml
    2.
    2. 合并icon_mapper_alt自定义映射
    3. 生成最终icon_mapper映射
    """

    @classmethod
    def parse_component_info(cls, component: str) -> str:
        """从appfilter.xml的ComponentInfo串提取包名

        Args:
            component: ComponentInfo字符串: "ComponentInfo{package/activity}"
        Returns:
            str: 包名, 失败返回空字符串
        Examples:
            parse_component_info("ComponentInfo{com.android.vending/activity}")
                Returns "com.android.vending"
        """
        match = re.match(r"ComponentInfo\{([^/]+)/.*?\}", component)
        if match:
            return match.group(1)
        return ""

    @classmethod
    def convert_icon_mapper(
        cls,
        appfilter_input_path: str,
        icon_mapper_output_path: str,
        icon_mapper_alt_path: str,
    ) -> None:
        """去重appfilter.xml, 合并icon_mapper_alt, 生成icon_mapper

        Args:
            appfilter_path: 原始appfilter.xml路径
            icon_mapper_path: 输出的映射文件路径
            icon_mapper_alt_path: 自定义映射文件路径
        """

        appfilter = Path(appfilter_input_path)
        icon_mapper_output = Path(icon_mapper_output_path)
        icon_mapper_alt = Path(icon_mapper_alt_path)

        if appfilter.exists():
            # 解析原始XML
            print(
                f"  (1/5) MappingProcessor.convert_icon_mapper: 已找到 appfilter ({appfilter})"
            )
            tree = ET.parse(appfilter)
            root = tree.getroot()
            unique_packages = {}

        # 处理每个item
        print("  (2/5) MappingProcessor.convert_icon_mapper: 正在去重 appfilter")
        for item in root.findall("item"):
            component = item.get("component", "")
            name = item.get("name", "")
            drawable = item.get("drawable", "")

            if component and drawable:
                package = cls.parse_component_info(component)
                if package:
                    unique_packages[package] = (name, drawable)

        # 合并icon_mapper_alt
        if icon_mapper_alt.exists():
            print(
                "  (3/5) MappingProcessor.convert_icon_mapper: 正在合并自定义映射 icon_mapper_alt"
            )
            alt_tree = ET.parse(icon_mapper_alt_path)
            alt_root = alt_tree.getroot()

            for item in alt_root.findall("item"):
                package = item.get("package", "")
                name = item.get("name", "")
                drawable = item.get("drawable", "")

                if package and drawable:
                    unique_packages[package] = (name, drawable)

        new_root = ET.Element("resources")

        for package, (name, drawable) in sorted(unique_packages.items()):
            new_item = ET.SubElement(new_root, "item")
            new_item.set("name", name)
            new_item.set("package", package)
            new_item.set("drawable", drawable)

        # 写入icon_mapper
        print("  (4/5) MappingProcessor.convert_icon_mapper: 正在生成 icon_mapper")
        tree = ET.ElementTree(new_root)
        with open(icon_mapper_output_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            rough_string = ET.tostring(new_root, encoding="unicode")
            formatted_string = ""
            indent = ""
            for line in rough_string.split(">"):
                if line.strip():
                    if not line.startswith("</"):
                        formatted_string += indent + line + ">\n"
                        if not line.startswith("<resources") and not line.endswith(
                            "/>"
                        ):
                            indent = "    "
                    else:
                        indent = ""
                        formatted_string += line + ">\n"

            f.write(formatted_string)

        if icon_mapper_output.exists():
            print(
                f"  (5/5) MappingProcessor.convert_icon_mapper: icon_mapper 映射文件已生成 ({icon_mapper_output_path})"
            )
