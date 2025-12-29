#!/usr/bin/env python3

import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import re
import sys

TOPICS_YAML = Path(__file__).parent / "topics.yaml"
PROTO_ROOT = Path(__file__).parent / "proto"

class Topic:
    def __init__(self, raw: dict):
        self._group = raw.get("_group", "")
        self._raw = raw
        self.ref = raw.get("ref")
        self.name = raw.get("name", "")
        self.schema = raw.get("schema", "")
        self.message = raw.get("message", "")
        self.description = raw.get("description", "")
        self.versions = raw.get("versions", [])


    def validate(self) -> List[str]:
        errors = []
        if not self._group or len(self._group) == 0:
            errors.append(f"❌ Topic name '{self.name}' has no service group.")
        if not self.name or "." not in self.name:
            errors.append(f"❌ Topic name '{self.name}' is invalid.")
        if not self.ref or not self.ref.isidentifier():
            errors.append(f"❌ Reference name '{self.ref}' is invalid or missing.")
        if self.schema and not Path(PROTO_ROOT / self.schema).exists():
            errors.append(f"❌ Schema file '{self.schema}' does not exist.")
        if self.message and "." not in self.message:
            errors.append(f"❌ Message '{self.message}' is invalid.")
        return errors
     
    def __str__(self):
        return str(self._raw)

def load_topics() -> List[Topic]:
    # with open(TOPICS_YAML, 'r', encoding='utf-8') as f:
    #     data = yaml.safe_load(f)

    # return [Topic(t) for t in data.get("topics", [])]
    with open(TOPICS_YAML, 'r', encoding='utf-8') as f:
        data = flatten_topics(yaml.safe_load(open("topics.yaml")))
    return [Topic(item) for item in data]

def flatten_topics(grouped_yaml: dict) -> List[Dict[str, Any]]:
    all_topics = []
    for group, topics in grouped_yaml.items():
        for t in topics:
            t["_group"] = group  # 可以在 check/gen-doc 中使用
            all_topics.append(t)
    return all_topics

# 使用



def check_topics(topics: List[Topic]):
    print("🔍 Checking topics...\n")

    all_errors = []
    name_set = set()
    message_index = {}       # {schema_path: set of message names}
    schema_package_map = {}  # {schema_path: package name}

    for topic in topics:
        if topic.schema:
            schema_path = PROTO_ROOT / topic.schema
            if schema_path.exists():
                content = schema_path.read_text(encoding="utf-8")
                
                # 提取 message 名
                message_matches = re.findall(r'message\s+(\w+)', content)
                message_index[str(schema_path)] = set(message_matches)

                # 提取 package 名
                pkg_match = re.search(r'package\s+([\w.]+);', content)
                if pkg_match:
                    schema_package_map[str(schema_path)] = pkg_match.group(1)

    for topic in topics:
        print(f" checking topic {topic.name} ...")
        errors = topic.validate()

        # 1️⃣ topic name 唯一性
        if topic.name in name_set:
            errors.append(f"❌ Duplicate topic name '{topic.name}'")
        else:
            name_set.add(topic.name)

        schema_path = PROTO_ROOT / topic.schema
        schema_str = str(schema_path)

        
        # 2️⃣ schema 文件存在
        if topic.schema and not schema_path.exists():
            errors.append(f"❌ Schema file not found: {topic.schema}")

        # 3️⃣ message 是否存在 + 包名是否一致
        if topic.schema and topic.message:
            if "." in topic.message:
                pkg, msg = topic.message.split(".", 1)
                defined_msgs = message_index.get(schema_str, set())
                defined_pkg = schema_package_map.get(schema_str)
                if msg not in defined_msgs:
                    errors.append(f"❌ Message '{msg}' not found in schema '{topic.schema}'")
                if defined_pkg and pkg != defined_pkg: 
                    errors.append(f"❌ Package mismatch: message declares '{pkg}', but schema declares '{defined_pkg}'")
            else:
                errors.append(f"❌ Message '{topic.message}' should include package prefix, e.g. 'user.LoginSuccessEvent'")

        if errors:
            print(f"⚠️ Topic '{topic.name}' has issues:")
            for e in errors:
                print("   ", e)
            all_errors.extend(errors)

    print("\n")

    if not all_errors:
        print("✅ All topics passed validation.")
        sys.exit(0)
    else:
        sys.exit(1)




def generate_doc(topics: List[Topic], format: str = "markdown"):
    if format != "markdown":
        raise ValueError("Only markdown supported.")
    print("# Kafka Topics Reference\n")
    print("# 说明\n")
    print("topics.yaml 里记录了每个微服务**发出**的topic事件及对应的protobuf数据结构描述\n")
    print("ref是引用的数据名称，name是topic字符串，name命令规则：service.entity.event\n")
    print("所有topic如下：\n\n")
    for topic in topics:
        print(f"## `{topic.name}`")
        print(f"- 📄 Schema: `{topic.schema}`")
        print(f"- 🧩 Message: `{topic.message}`")
        print(f"- 🧷 Ref: `{topic.ref}`")
        print(f"- 📝 Description: {topic.description}")
        print(f"- 🏷  Versions: {', '.join(topic.versions)}\n")

def generate_code(topics: List[Topic], lang: str):
    ext_map = {"go": "go_out", "python": "python_out"}
    opt_map = {"go": "--go_opt=paths=source_relative", "python": ""}
    if lang not in ext_map and lang != "all":
        raise ValueError(f"Unsupported language: {lang}")
    if lang == "all":
        langs = ext_map.keys()
    else:
        langs = [lang]
    for lang in langs:
        for topic in topics:
            if not topic.schema:
                continue
            schema_path = PROTO_ROOT / topic.schema
            print(f"protoc --proto_path=proto --{ext_map[lang]}=generated/{lang} {opt_map[lang]} {schema_path}")

def camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.upper()

def generate_constants(topics: List[Topic], lang: str):
    if lang in ["go", "all"]:
        lines = ["// Code generated by parse_topics.py. DO NOT EDIT.\n", "package protobuf\n\n"]
        for t in topics:
            errors = t.validate()
            if errors:
                print(f"⚠️ Skipping invalid topic {t.name}:")
                for e in errors:
                    print("   ", e)
                continue
            lines.append(f'const {camel_to_snake(t.ref)} = "{t.name}"\n')
        output_file = Path("./topics.go")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("".join(lines), encoding="utf-8")
        print(f"✅ Go constants written to {output_file}")

    if lang in ["python", "all"]:
        lines = ["# Code generated by parse_topics.py. DO NOT EDIT.\n\n"]
        for t in topics:
            errors = t.validate()
            if errors:
                print(f"⚠️ Skipping invalid topic {t.name}:")
                for e in errors:
                    print("   ", e)
                continue
            lines.append(f'{camel_to_snake(t.ref)} = "{t.name}"\n')
        output_file = Path("./topics.py")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("".join(lines), encoding="utf-8")
        print(f"✅ Python constants written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Kafka Topic Utilities")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="Validate topics.yaml")

    doc_parser = sub.add_parser("gen-doc", help="Generate markdown docs")
    doc_parser.add_argument("--format", default="markdown")

    code_parser = sub.add_parser("gen-code", help="Generate protoc commands")
    code_parser.add_argument("--lang", required=True, choices=["go", "python", "all"])

    const_parser = sub.add_parser("gen-const", help="Generate topic constants")
    const_parser.add_argument("--lang", required=True, choices=["go", "python", "all"])

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    topics = load_topics()

    if args.command == "check":
        check_topics(topics)
    elif args.command == "gen-doc":
        generate_doc(topics, args.format)
    elif args.command == "gen-code":
        generate_code(topics, args.lang)
    elif args.command == "gen-const":
        generate_constants(topics, args.lang)

if __name__ == "__main__":
    main()
