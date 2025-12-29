#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TSON转换命令行工具

用法:
    pixelarraylib tson_convert <input_file> [--output <output_file>] [--to-json]
    pixelarraylib tson_convert --json-to-tson <json_string>
    pixelarraylib tson_convert --tson-to-json <tson_string>
"""

import argparse
import sys
from pixelarraylib.system.tson import Tson


def main():
    parser = argparse.ArgumentParser(
        description="TSON (Token-Optimized JSON) 转换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 将JSON文件转换为TSON文件
  pixelarraylib tson_convert data.json
  
  # 将TSON文件转换为JSON文件
  pixelarraylib tson_convert data.tson --to-json
  
  # 指定输出文件
  pixelarraylib tson_convert input.json --output output.tson
  
  # 直接转换字符串
  pixelarraylib tson_convert --json-to-tson '{"name":"test","age":30}'
  pixelarraylib tson_convert --tson-to-json '{name:"test",age:30}'
        """,
    )
    
    parser.add_argument(
        "input_file",
        nargs="?",
        help="输入文件路径（JSON或TSON格式）",
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（如果不指定，将自动生成）",
    )
    
    parser.add_argument(
        "--to-json",
        action="store_true",
        help="将TSON转换为JSON（默认是将JSON转换为TSON）",
    )
    
    parser.add_argument(
        "--json-to-tson",
        help="直接转换JSON字符串为TSON",
    )
    
    parser.add_argument(
        "--tson-to-json",
        help="直接转换TSON字符串为JSON",
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="格式化输出JSON（仅在--tson-to-json时有效）",
    )
    
    args = parser.parse_args()
    
    # 创建 Tson 实例
    tson = Tson()
    
    # 处理直接字符串转换
    if args.json_to_tson:
        try:
            result = tson.json_to_tson(args.json_to_tson)
            print(result)
            return
        except Exception as e:
            print(f"错误: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    if args.tson_to_json:
        try:
            result = tson.tson_to_json(args.tson_to_json, pretty=args.pretty)
            if isinstance(result, str):
                print(result)
            else:
                import json
                print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
            return
        except Exception as e:
            print(f"错误: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    # 处理文件转换
    if not args.input_file:
        parser.print_help()
        sys.exit(1)
    
    try:
        output_file = tson.convert_file(
            args.input_file,
            args.output,
            to_tson=not args.to_json
        )
        print(f"转换成功！输出文件: {output_file}")
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

