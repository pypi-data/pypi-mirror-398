from v0.relationalai.semantics.internal import Fragment
from v0.relationalai.semantics.rel import Compiler as RelCompiler
from v0.relationalai.semantics.metamodel import ir
from v0.relationalai.semantics.sql import Compiler as SqlCompiler

from dataclasses import dataclass
from typing import Optional
import inspect
import tempfile
import webbrowser
import os
import html

@dataclass
class CompilationResult:
    python_source: str
    ir: str
    rel: Optional[str]
    sql: Optional[str]

    def show(self):
        """
        Displays the compilation results in a browser by creating a temporary HTML file.

        Args:
            compilation_result: Dictionary containing 'ir', 'rel', and 'sql' keys
                               as returned by the compile() function

        Returns:
            Path to the temporary HTML file
        """

        # Create HTML content with syntax highlighting using highlight.js
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAI Compilation Results</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/python.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/ruby.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/sql.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 30px; }}
                h2 {{ color: #333; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow: auto; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>RAI Compilation Results</h1>

            <div class="section">
                <h2>Python Source</h2>
                <pre><code class="language-python">{}</code></pre>
            </div>

            <div class="section">
                <h2>IR (Intermediate Representation)</h2>
                <pre><code class="language-json">{}</code></pre>
            </div>

            <div class="section">
                <h2>Rel</h2>
                <pre><code class="language-ruby">{}</code></pre>
            </div>

            <div class="section">
                <h2>SQL</h2>
                <pre><code class="language-sql">{}</code></pre>
            </div>

            <script>hljs.highlightAll();</script>
        </body>
        </html>
        """.format(
            html.escape(self.python_source),
            html.escape(self.ir),
            html.escape(self.rel or "not available"),
            html.escape(self.sql or "not available"),
        )

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            f.write(html_content.encode('utf-8'))
            temp_path = f.name

        # Open the HTML file in the default browser
        webbrowser.open('file://' + os.path.abspath(temp_path))

        return temp_path

class CompilationManager:
    def __init__(self, fragment: Fragment):
        self.fragment = fragment

    def python_source(self):
        """Extract the source code that created this fragment from the caller's file."""
        try:
            # Start with the current frame and work backwards
            frame = inspect.currentframe()

            # Skip the first frame (this method)
            if frame:
                frame = frame.f_back

            relevant_frames = []
            max_frames_to_check = 10  # Limit how far back we go

            # Collect frames that might be relevant
            for i in range(max_frames_to_check):
                if frame is None:
                    break

                filename = frame.f_code.co_filename

                # Skip frames from internal Python modules
                if (not filename.startswith('<') and
                    'site-packages' not in filename and
                    '/lib/python' not in filename):

                    # Check whether this file imports from relationalai.semantics.internal
                    try:
                        with open(filename, 'r') as f:
                            content = f.read()
                            if ('from relationalai.semantics.internal' in content or
                                'import relationalai.semantics.internal' in content):
                                relevant_frames.append(frame)
                    except FileNotFoundError:
                        pass  # If we can't read the file, just continue

                frame = frame.f_back

            # If we found relevant frames, use the last one (furthest up the call stack)
            if relevant_frames:
                frame = relevant_frames[-1]
            else:
                # Fall back to the second frame if we didn't find any relevant ones
                frame = inspect.currentframe()
                for _ in range(2):
                    if frame is None:
                        return "Source code not available"
                    frame = frame.f_back

            if frame is None:
                return "Source code not available"

            # Get the filename and line number
            caller_info = inspect.getframeinfo(frame)
            filename = caller_info.filename
            lineno = caller_info.lineno

            # Read the source file
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    source_lines = f.readlines()

                # Extract a reasonable context around the line
                start_line = max(0, lineno - 20)
                end_line = min(len(source_lines), lineno + 20)

                # Try to find a complete test method or function
                # Look for the start of a function or method definition before the current line
                for i in range(lineno - 1, max(0, start_line - 10), -1):
                    if i >= len(source_lines):
                        continue
                    line = source_lines[i].strip()
                    if line.startswith('def ') or line.startswith('async def '):
                        start_line = i
                        break

                context_lines = source_lines[start_line:end_line]
                return ''.join(context_lines)

            return "Source file not found"
        except Exception as e:
            return f"Error extracting source code: {str(e)}"

    def ir(self):
        builder_model = self.fragment._model
        if not builder_model:
            raise ValueError("Fragment must be part of a model to compile to IR")
        ir_model = builder_model._to_ir()
        # TODO: do something with the fragment here
        # fragment_task = builder_model._compiler.compile_task(self.fragment)
        return ir_model

    def rel(self, ir_model=None):
        if ir_model is None:
            ir_model = self.ir()
        rel_compiler = RelCompiler()
        full_code = rel_compiler.compile(ir_model)
        return full_code

    def sql(self, ir_model=None):
        if ir_model is None:
            ir_model = self.ir()
        return SqlCompiler().compile(ir_model)

    def compile(self):
        """
        Sends the various compiled forms of a fragment to the debugger.
        This function compiles the fragment to IR, Rel, and SQL, then logs
        the results to the debug system.

        Returns:
            Dictionary containing 'ir', 'rel', and 'sql' keys with the compiled outputs
        """
        try:
            ir_model = self.ir()
            ir_string = ir.node_to_string(ir_model)

            python_source = self.python_source()

            try:
                rel = self.rel(ir_model)
            except Exception:
                rel = None

            try:
                sql = self.sql(ir_model)
            except Exception:
                sql = None

            return CompilationResult(python_source, ir_string, rel, sql)
        except Exception as e:
            raise e

    def display(self, compilation_result):
        """
        Displays the compilation results in a browser by creating a temporary HTML file.

        Args:
            compilation_result: Dictionary containing 'ir', 'rel', and 'sql' keys
                               as returned by the compile() function

        Returns:
            Path to the temporary HTML file
        """
        # Create HTML content with syntax highlighting using highlight.js
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAI Compilation Results</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/sql.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 30px; }}
                h2 {{ color: #333; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow: auto; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>RAI Compilation Results</h1>

            <div class="section">
                <h2>IR (Intermediate Representation)</h2>
                <pre><code class="language-json">{}</code></pre>
            </div>

            <div class="section">
                <h2>Rel</h2>
                <pre><code class="language-sql">{}</code></pre>
            </div>

            <div class="section">
                <h2>SQL</h2>
                <pre><code class="language-sql">{}</code></pre>
            </div>

            <script>hljs.highlightAll();</script>
        </body>
        </html>
        """.format(
            html.escape(compilation_result.get('ir', 'Not available')) if compilation_result.get('ir') else '<span class="error">Error during IR compilation</span>',
            html.escape(compilation_result.get('rel', 'Not available')) if compilation_result.get('rel') else '<span class="error">Error during Rel compilation</span>',
            html.escape(compilation_result.get('sql', 'Not available')) if compilation_result.get('sql') else '<span class="error">Error during SQL compilation</span>'
        )

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            f.write(html_content.encode('utf-8'))
            temp_path = f.name

        # Open the HTML file in the default browser
        webbrowser.open('file://' + os.path.abspath(temp_path))

        return temp_path
