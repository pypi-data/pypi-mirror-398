"""
Unit tests for autocoder.rag.terminal.args

这些测试覆盖 create_parser 和 parse_arguments 的核心与边界行为。

注意：下方在功能级别添加了类似 JSDoc 的注释块以详细说明测试目标与预期。
"""

import argparse
import builtins
import importlib
from types import SimpleNamespace
from unittest.mock import patch

import pytest

# Target module under test
from autocoder.rag.terminal import args as args_module


# ----------------------------------------------------------------------------
# JSDoc-like description for create_parser tests
# ----------------------------------------------------------------------------
# /**
#  * Function: create_parser
#  * Purpose:
#  *   - 构建顶层 argparse.ArgumentParser，并注册以下子命令：
#  *     build_hybrid_index, serve, run, benchmark, tools
#  *   - 根据系统语言选择多语言描述，并设定 tokenizer_path 默认值
#  * Key Inputs:
#  *   - locale.getdefaultlocale() 影响多语言描述选择
#  *   - importlib.resources.files 控制 tokenizer_path 的存在与否
#  * Expected Behavior:
#  *   - 返回对象类型为 argparse.ArgumentParser
#  *   - parser._actions 中包含 SubParsersAction，且 choices 覆盖所有子命令
#  *   - 子命令各自的参数默认值与类型正确（int/float/str/list/flags）
#  */


def _get_subparsers(parser: argparse.ArgumentParser):
    """Return the dict of subparsers choices for convenience."""
    subparsers_actions = [
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    ]
    return subparsers_actions[0].choices if subparsers_actions else {}


@pytest.fixture()
def zh_locale():
    """Mock zh_CN locale to ensure desc uses Chinese mapping."""
    with patch("locale.getdefaultlocale", return_value=("zh_CN", "UTF-8")):
        yield


@pytest.fixture()
def en_locale():
    """Mock en_US locale to ensure desc uses English mapping."""
    with patch("locale.getdefaultlocale", return_value=("en_US", "UTF-8")):
        yield


@pytest.fixture()
def tokenizer_exists():
    """Mock tokenizer file path exists and returns a deterministic path."""
    # resources.files("autocoder") / "data" / "tokenizer.json"
    class DummyPath(str):
        def __truediv__(self, other):
            return DummyPath(f"{self}/{other}")

    def files(pkg):
        return DummyPath("/mock/autocoder/data")

    with patch("importlib.resources.files", side_effect=files):
        yield


@pytest.fixture()
def tokenizer_missing():
    """Mock tokenizer path resolution raises FileNotFoundError to produce None default."""
    with patch("importlib.resources.files", side_effect=FileNotFoundError):
        yield


# ----------------------------------------------------------------------------
# /**
#  * Test: create_parser_basic_structure
#  * Verify:
#  *   - 返回 parser 且包含预期子命令集合
#  */
# ----------------------------------------------------------------------------

def test_create_parser_basic_structure(en_locale, tokenizer_exists):
    parser = args_module.create_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    choices = _get_subparsers(parser)
    assert set(choices.keys()) == {
        "build_hybrid_index", "serve", "run", "benchmark", "tools"
    }


# ----------------------------------------------------------------------------
# /**
#  * Test: create_parser_tokenizer_default
#  * Verify:
#  *   - 当 tokenizer 存在时，相关参数默认值为路径字符串
#  *   - 当 tokenizer 缺失时，相关参数默认值为 None
#  */
# ----------------------------------------------------------------------------

def test_create_parser_tokenizer_default_present(en_locale, tokenizer_exists):
    parser = args_module.create_parser()
    choices = _get_subparsers(parser)

    # Inspect some subparsers for default of --tokenizer_path
    for name in ["build_hybrid_index", "serve", "run", "tools"]:
        sp = choices[name]
        # Collect defaults from parser
        defaults = sp.parse_args([])
        assert getattr(defaults, "tokenizer_path", None) is not None
        assert isinstance(defaults.tokenizer_path, str)


def test_create_parser_tokenizer_default_missing(en_locale, tokenizer_missing):
    parser = args_module.create_parser()
    choices = _get_subparsers(parser)

    for name in ["build_hybrid_index", "serve", "run", "tools"]:
        sp = choices[name]
        defaults = sp.parse_args([])
        # When missing, default should be None
        assert getattr(defaults, "tokenizer_path", None) is None


# ----------------------------------------------------------------------------
# /**
#  * Test: serve_defaults_and_types
#  * Verify:
#  *   - serve 子命令参数的默认值与类型
#  *   - 包含边界型浮点数与列表默认值
#  */
# ----------------------------------------------------------------------------

def test_serve_defaults_and_types(en_locale, tokenizer_missing):
    parser = args_module.create_parser()
    serve = _get_subparsers(parser)["serve"]
    args = serve.parse_args([])

    # Flag defaults
    assert args.quick is False
    assert args.allow_credentials is False
    assert args.enable_local_image_host is False
    assert args.agentic is False
    assert args.enable_hybrid_index is False
    assert args.without_contexts is False

    # Types and defaults
    assert isinstance(args.port, int) and args.port == 8000
    assert isinstance(args.index_filter_workers, int) and args.index_filter_workers == 100
    assert isinstance(args.index_filter_file_num, int) and args.index_filter_file_num == 3
    assert isinstance(args.rag_context_window_limit, int) and args.rag_context_window_limit == 56000
    assert isinstance(args.full_text_ratio, float) and args.full_text_ratio == 0.7
    assert isinstance(args.segment_ratio, float) and args.segment_ratio == 0.2
    assert isinstance(args.allowed_origins, list) and args.allowed_origins == ["*"]
    assert isinstance(args.allowed_methods, list) and args.allowed_methods == ["*"]
    assert isinstance(args.allowed_headers, list) and args.allowed_headers == ["*"]
    assert isinstance(args.product_mode, str) and args.product_mode == "pro"
    assert isinstance(args.rag_storage_type, str) and args.rag_storage_type == "duckdb"

    # Out-of-range boundary acceptance (no validation enforced by argparse)
    args2 = serve.parse_args([
        "--full_text_ratio", "1.5", "--segment_ratio", "-0.1"
    ])
    assert pytest.approx(args2.full_text_ratio, 1.5)
    assert pytest.approx(args2.segment_ratio, -0.1)


# ----------------------------------------------------------------------------
# /**
#  * Test: run_required_doc_dir
#  * Verify:
#  *   - run 子命令必须提供 --doc_dir，否则解析失败
#  */
# ----------------------------------------------------------------------------

def test_run_required_doc_dir(en_locale, tokenizer_missing):
    parser = args_module.create_parser()
    run_parser = _get_subparsers(parser)["run"]

    # Omit required --doc_dir should raise SystemExit from argparse
    with pytest.raises(SystemExit):
        run_parser.parse_args(["--model", "v3_chat"])  # missing --doc_dir

    # Provide required value should pass
    args = run_parser.parse_args(["--doc_dir", "/tmp/docs"])  # defaults for others
    assert args.doc_dir == "/tmp/docs"
    assert args.product_mode == "lite"  # default for run


# ----------------------------------------------------------------------------
# /**
#  * Function: parse_arguments
#  * Purpose:
#  *   - 创建 parser 并解析传入的 input_args
#  *   - 返回 (args, parser, subparsers_dict)
#  * Expected Behavior:
#  *   - subparsers_dict 含有各子命令 parser 引用
#  */
# ----------------------------------------------------------------------------

def test_parse_arguments_returns_structures(en_locale, tokenizer_missing):
    # Use serve command to verify proper dispatch
    input_args = [
        "serve", "--port", "9000", "--allowed_origins", "*"
    ]
    args, parser, subparsers_dict = args_module.parse_arguments(input_args)

    assert isinstance(parser, argparse.ArgumentParser)
    assert isinstance(subparsers_dict, dict)
    assert set(subparsers_dict.keys()) == {
        "build_hybrid_index", "serve", "run", "benchmark", "tools"
    }

    assert args.port == 9000
    assert args.allowed_origins == "*"  # Note: direct list default is ["*"], but passing overrides with str


# ----------------------------------------------------------------------------
# /**
#  * Test: build_hybrid_index_defaults
#  * Verify:
#  *   - 默认值与类型，以及布尔/字符串/int 的组合
#  */
# ----------------------------------------------------------------------------

def test_build_hybrid_index_defaults(en_locale, tokenizer_missing):
    parser = args_module.create_parser()
    build = _get_subparsers(parser)["build_hybrid_index"]
    args = build.parse_args([])

    assert args.rag_storage_type == "duckdb"
    assert isinstance(args.rag_index_build_workers, int) and args.rag_index_build_workers == 5
    assert args.quick is False
    assert args.file == ""
    assert args.model == "v3_chat"
    assert args.on_ray is False
    assert args.source_dir == "."
    assert args.doc_dir == ""
    assert args.enable_hybrid_index is False


# ----------------------------------------------------------------------------
# /**
#  * Test: benchmark_defaults
#  * Verify:
#  *   - 类型与默认值
#  */
# ----------------------------------------------------------------------------

def test_benchmark_defaults(en_locale):
    parser = args_module.create_parser()
    bench = _get_subparsers(parser)["benchmark"]
    args = bench.parse_args([])

    assert args.model == "v3_chat"
    assert isinstance(args.parallel, int) and args.parallel == 10
    assert isinstance(args.rounds, int) and args.rounds == 1
    assert args.type == "byzerllm"
    assert args.api_key == ""
    assert args.base_url == ""
    assert isinstance(args.query, str) and "how are you" in args.query


# ----------------------------------------------------------------------------
# /**
#  * Test: tools_defaults
#  * Verify:
#  *   - 顶层 tools 参数默认值，以及子工具 count/chunk/recall 的必需参数与默认行为
#  */
# ----------------------------------------------------------------------------

def test_tools_defaults_and_subtools(en_locale, tokenizer_missing):
    parser = args_module.create_parser()
    tools = _get_subparsers(parser)["tools"]

    # Top level defaults
    top_args = tools.parse_args(["count", "--file", "README.md"])  # route to subtool
    assert top_args.product_mode == "pro"  # default at tools level

    # count subtool requires --file
    with pytest.raises(SystemExit):
        tools.parse_args(["count"])  # missing --file

    # recall subtool requires --model
    with pytest.raises(SystemExit):
        tools.parse_args(["recall"])  # missing --model

    # chunk subtool requires --model
    with pytest.raises(SystemExit):
        tools.parse_args(["chunk"])  # missing --model


# ----------------------------------------------------------------------------
# /**
#  * Test: locale_switching
#  * Verify:
#  *   - 不同 locale 下 create_parser 不抛异常（国际化描述映射可用）
#  */
# ----------------------------------------------------------------------------

def test_locale_switching(zh_locale, tokenizer_missing):
    parser = args_module.create_parser()
    choices = _get_subparsers(parser)
    assert "serve" in choices and "run" in choices
