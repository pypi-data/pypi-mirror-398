"""Tests for the discover module."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from flightline.cli import cli
from flightline.discover.detect import (
    detect_js_ai_calls,
    detect_python_ai_calls,
)
from flightline.discover.heuristics import detect_heuristic_calls
from flightline.discover.ingest import detect_project_signals, enumerate_files
from flightline.discover.schema import (
    CallType,
    Provider,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def python_openai_file(temp_dir):
    """Create a Python file with OpenAI usage."""
    content = '''
from openai import OpenAI

client = OpenAI()

def classify_email(email_body: str, customer_record: dict) -> str:
    """Classify an email using AI."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an email classifier."},
            {"role": "user", "content": f"Classify this email: {email_body}"}
        ],
        response_format={"type": "json_object"}
    )
    
    result = response.choices[0].message.content
    
    if result == "urgent":
        return "priority"
    elif result == "spam":
        return "trash"
    else:
        return "inbox"
'''
    file_path = temp_dir / "classify.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def python_anthropic_file(temp_dir):
    """Create a Python file with Anthropic usage."""
    content = '''
from anthropic import Anthropic

client = Anthropic()

def summarize_document(doc_content: str) -> str:
    """Summarize a document using Claude."""
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"Summarize this document: {doc_content}"}
        ]
    )
    
    return message.content[0].text
'''
    file_path = temp_dir / "summarize.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def js_openai_file(temp_dir):
    """Create a JS file with OpenAI usage."""
    content = """
import OpenAI from "openai";

const client = new OpenAI();

async function analyzeRequest(requestBody) {
    const response = await client.chat.completions.create({
        model: "gpt-4",
        messages: [
            { role: "system", content: "Analyze the request." },
            { role: "user", content: requestBody }
        ]
    });
    
    const result = response.choices[0].message.content;
    
    if (result === "approved") {
        return processApproval(result);
    }
    
    return result;
}

function processApproval(data) {
    console.log("Processing:", data);
}
"""
    file_path = temp_dir / "analyze.js"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def ts_anthropic_file(temp_dir):
    """Create a TS file with Anthropic usage."""
    content = """
import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic();

export async function generateResponse(prompt: string): Promise<string> {
    const message = await anthropic.messages.create({
        model: "claude-3-opus-20240229",
        max_tokens: 1024,
        messages: [{ role: "user", content: prompt }]
    });
    
    return message.content[0].text;
}
"""
    file_path = temp_dir / "generate.ts"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def python_openrouter_file(temp_dir):
    """Create a Python file with OpenRouter usage."""
    content = """
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-..."
)

def ask_openrouter(prompt):
    return client.chat.completions.create(
        model="google/gemini-pro",
        messages=[{"role": "user", "content": prompt}]
    )
"""
    file_path = temp_dir / "openrouter.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def js_google_file(temp_dir):
    """Create a JS file with Google Gemini usage."""
    content = """
import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI("API_KEY");
const model = genAI.getGenerativeModel({ model: "gemini-pro" });

async function run() {
  const result = await model.generateContent("Explain AI");
  console.log(result.response.text());
}
"""
    file_path = temp_dir / "google.js"
    file_path.write_text(content)
    return file_path


# =============================================================================
# INGEST TESTS
# =============================================================================


class TestIngest:
    """Tests for file ingestion."""

    def test_enumerate_files_respects_gitignore(self, temp_dir):
        """Should skip files matching .gitignore patterns."""
        # Create .gitignore
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("ignored.py\n*.test.js\n")

        # Create files
        (temp_dir / "included.py").write_text("print('hello')")
        (temp_dir / "ignored.py").write_text("print('ignored')")
        (temp_dir / "test.test.js").write_text("// ignored")
        (temp_dir / "real.js").write_text("// included")

        index = enumerate_files(temp_dir)

        file_names = {f.name for f in index.files}
        assert "included.py" in file_names
        assert "real.js" in file_names
        assert "ignored.py" not in file_names
        assert "test.test.js" not in file_names

    def test_enumerate_files_detects_languages(self, temp_dir):
        """Should detect languages from file extensions."""
        (temp_dir / "app.py").write_text("# python")
        (temp_dir / "app.ts").write_text("// typescript")
        (temp_dir / "app.js").write_text("// javascript")

        index = enumerate_files(temp_dir)

        assert "python" in index.languages
        assert "typescript" in index.languages
        assert "javascript" in index.languages

    def test_enumerate_files_respects_language_filter(self, temp_dir):
        """Should filter by requested languages."""
        (temp_dir / "app.py").write_text("# python")
        (temp_dir / "app.ts").write_text("// typescript")

        index = enumerate_files(temp_dir, languages={"python"})

        assert len(index.files) == 1
        assert index.files[0].suffix == ".py"

    def test_detect_project_signals_package_json(self, temp_dir):
        """Should detect AI SDKs from package.json."""
        package_json = temp_dir / "package.json"
        package_json.write_text("""{
            "dependencies": {
                "openai": "^4.0.0",
                "zod": "^3.0.0"
            }
        }""")

        signals = detect_project_signals(temp_dir)

        assert "openai" in signals.ai_sdks
        assert "zod" in signals.validation_libraries


# =============================================================================
# PYTHON DETECTION TESTS
# =============================================================================


class TestPythonDetection:
    """Tests for Python AI call detection."""

    def test_detect_openai_chat_call(self, python_openai_file):
        """Should detect OpenAI chat completions call."""
        calls = detect_python_ai_calls(python_openai_file)

        assert len(calls) == 1
        call = calls[0]

        assert call.provider == Provider.OPENAI
        assert call.call_type == CallType.CHAT
        assert call.location.function == "classify_email"

    def test_detect_openrouter_call(self, python_openrouter_file):
        """Should detect OpenRouter via base_url."""
        calls = detect_python_ai_calls(python_openrouter_file)

        assert len(calls) == 1
        assert calls[0].provider == Provider.OPENROUTER

    def test_detect_anthropic_messages_call(self, python_anthropic_file):
        """Should detect Anthropic messages call."""
        calls = detect_python_ai_calls(python_anthropic_file)

        assert len(calls) == 1
        call = calls[0]

        assert call.provider == Provider.ANTHROPIC
        assert call.call_type == CallType.CHAT
        assert call.location.function == "summarize_document"

    def test_no_false_positives(self, temp_dir):
        """Should not detect calls in non-AI code."""
        content = """
def create():
    return {"type": "chat"}

class Chat:
    def completions(self):
        pass
"""
        file_path = temp_dir / "noai.py"
        file_path.write_text(content)

        calls = detect_python_ai_calls(file_path)
        assert len(calls) == 0


# =============================================================================
# JAVASCRIPT DETECTION TESTS
# =============================================================================


class TestJavaScriptDetection:
    """Tests for JavaScript/TypeScript AI call detection."""

    def test_detect_openai_chat_call(self, js_openai_file):
        """Should detect OpenAI chat completions call."""
        calls = detect_js_ai_calls(js_openai_file)

        assert len(calls) == 1
        call = calls[0]

        assert call.provider == Provider.OPENAI
        assert call.call_type == CallType.CHAT

    def test_detect_anthropic_messages_call(self, ts_anthropic_file):
        """Should detect Anthropic messages call."""
        calls = detect_js_ai_calls(ts_anthropic_file)

        assert len(calls) == 1
        call = calls[0]

        assert call.provider == Provider.ANTHROPIC
        assert call.call_type == CallType.CHAT

    def test_detect_google_gemini_call(self, js_google_file):
        """Should detect Google Gemini call."""
        calls = detect_js_ai_calls(js_google_file)

        assert len(calls) == 1
        assert calls[0].provider == Provider.GOOGLE

    def test_no_false_positives_js(self, temp_dir):
        """Should not detect calls in non-AI code."""
        content = """
function chat() {
    return { completions: { create: () => {} } };
}

const messages = { create: () => {} };
"""
        file_path = temp_dir / "noai.js"
        file_path.write_text(content)

        calls = detect_js_ai_calls(file_path)
        assert len(calls) == 0


# =============================================================================
# HEURISTIC DETECTION TESTS
# =============================================================================


class TestHeuristicDetection:
    """Tests for heuristic AI footprint detection."""

    def test_detect_custom_wrapper(self, temp_dir):
        """Should detect custom wrappers via parameter footprints."""
        content = """
async def ask_our_robot(prompt, context):
    return await my_internal_service.call({
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    })
"""
        file_path = temp_dir / "custom.py"
        file_path.write_text(content)

        calls = detect_heuristic_calls(file_path)
        assert len(calls) >= 1
        assert calls[0].provider == Provider.UNKNOWN
        assert calls[0].location.function == "ask_our_robot"

    def test_detect_langchain_style(self, temp_dir):
        """Should detect LangChain-style message patterns."""
        content = """
const messages = [
    { role: "human", content: "What is the capital of France?" },
    { role: "ai", content: "Paris" }
];
const result = await chain.invoke({ 
    messages,
    temperature: 0,
    model: "claude-3"
});
"""
        file_path = temp_dir / "chain.js"
        file_path.write_text(content)

        calls = detect_heuristic_calls(file_path)
        assert len(calls) >= 1


# =============================================================================
# CLI TESTS
# =============================================================================


class TestDiscoverCLI:
    """Tests for the discover CLI command."""

    def test_discover_help(self):
        """Discover command should show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", "--help"])

        assert result.exit_code == 0
        assert "Discover AI operations" in result.output

    def test_scan_alias(self):
        """Scan should be an alias for discover."""
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", "--help"])

        assert result.exit_code == 0
        assert "Discover AI operations" in result.output

    def test_discover_empty_dir(self, temp_dir):
        """Discover on empty dir should handle gracefully."""
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", str(temp_dir), "--json"])

        # Should complete without error
        assert result.exit_code == 0

    def test_discover_finds_ai_calls(self, temp_dir, python_openai_file):
        """Discover should find AI calls and output JSON."""
        runner = CliRunner()
        out_file = temp_dir / "discovery.json"

        result = runner.invoke(cli, ["discover", str(temp_dir), "-o", str(out_file), "--json"])

        assert result.exit_code == 0
        assert out_file.exists()

        import json

        with open(out_file) as f:
            data = json.load(f)

        assert "nodes" in data
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["provider"] == "openai"


# =============================================================================
# INTEGRATION TEST
# =============================================================================


class TestIntegration:
    """Integration tests using real repo code."""

    def test_discover_on_backend(self):
        """Discover should work on the actual backend directory."""
        # The backend has real OpenAI usage in learn.py
        backend_path = Path(__file__).parent.parent.parent / "backend"

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        runner = CliRunner()
        result = runner.invoke(cli, ["discover", str(backend_path), "--json"])

        # Should complete successfully
        assert result.exit_code == 0

        import json

        data = json.loads(result.output)

        # Backend should have AI operations
        assert "nodes" in data

    def test_discover_on_cli(self):
        """Discover should find AI calls in the CLI code itself."""
        cli_path = Path(__file__).parent.parent

        runner = CliRunner()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_file = Path(f.name)

        try:
            result = runner.invoke(cli, ["discover", str(cli_path), "-o", str(out_file), "--json"])

            assert result.exit_code == 0

            import json

            with open(out_file) as f:
                data = json.load(f)

            # CLI has OpenAI usage in learn.py and generate.py
            assert "nodes" in data
            assert len(data["nodes"]) >= 1  # At least learn.py

            # Check that we found OpenAI calls
            providers = {node["provider"] for node in data["nodes"]}
            assert "openai" in providers
        finally:
            out_file.unlink(missing_ok=True)
