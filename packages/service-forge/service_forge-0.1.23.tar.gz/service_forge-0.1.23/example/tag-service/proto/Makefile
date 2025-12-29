PROTO_DIR = proto
GO_OUT_DIR = .
PY_OUT_DIR = .
PROTO_FILES = $(shell find $(PROTO_DIR) -name "*.proto")
TOPIC_TOOL = python parse_topics.py

# === check ===
check:
	@echo "🔍 Checking topics.yaml..."
	@$(TOPIC_TOOL) check

# === proto 生成（依赖 check） ===
gen-proto-go: clean check
	@echo "📦 Generating Go protobuf files..."
	@mkdir -p $(GO_OUT_DIR)
	@for file in $(shell find $(PROTO_DIR) -name "*.proto"); do \
		protoc \
			--proto_path=$(PROTO_DIR) \
			--go_out=$(GO_OUT_DIR) \
			--go_opt=paths=source_relative \
			$$file; \
	done

gen-proto-python: clean check
	@echo "🐍 Generating Python protobuf files..."
	@mkdir -p $(PY_OUT_DIR)
	@for file in $(shell find $(PROTO_DIR) -name "*.proto"); do \
		protoc \
			--proto_path=$(PROTO_DIR) \
			--pyi_out=$(PY_OUT_DIR) \
			--python_out=$(PY_OUT_DIR) \
			$$file; \
	done

# === 常量生成（依赖 check） ===
gen-const-go: clean check
	@echo "🔧 Generating Go topic constants..."
	@$(TOPIC_TOOL) gen-const --lang=go

gen-const-python: clean check
	@echo "🔧 Generating Python topic constants..."
	@$(TOPIC_TOOL) gen-const --lang=python

# === 文档生成（依赖 check） ===
gen-doc: check
	@echo "🔧 Generating Docs..."
	@$(TOPIC_TOOL) gen-doc > README.md

# === 删除生成的代码，用于重新生成 ===
clean:
	@echo "🧹 Cleaning generated files..."
	@find . -mindepth 1 -maxdepth 1 -type d ! -name proto ! -name '.*' -exec rm -rf {} +
	@rm -f topics.go topics.py
# === 一键生成 ===
all: check gen-proto-go gen-proto-python gen-const-go gen-const-python gen-doc