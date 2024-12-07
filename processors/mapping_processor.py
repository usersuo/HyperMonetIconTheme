import re
import xml.etree.ElementTree as ET

from pathlib import Path


class MappingProcessor:
    # 提取原始Appfilter中ComponentInfo的包名
    @staticmethod
    def parse_component_info(component: str) -> str:
        match = re.match(r"ComponentInfo\{([^/]+)/.*?\}", component)
        if match:
            return match.group(1)
        return ""

    # 去重并生成icon_mapper
    @staticmethod
    def convert_icon_mapper(
        appfilter_input_path: str,
        icon_mapper_output_path: str,
        icon_mapper_alt_path: str,
    ) -> None:
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
                package = MappingProcessor.parse_component_info(component)
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
