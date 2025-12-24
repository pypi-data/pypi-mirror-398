import os
import sys
import warnings
import more_itertools
from .tracing import get_tracer
from .error import Diagnostic, RAIWarning, RichEmitter, HTMLEmitter, RAIException
import traceback

#------------------------------------------------------
# Base Env
#------------------------------------------------------

class EnvBase:
    """Decides renderer and how to deliver the string. Override to suit your runtime."""
    # Which renderer to use for this env
    prefers_html: bool = False
    seen_diagnostics: set[str] = set()

    def is_active(self) -> bool:  # override
        return False

    def renderer(self):
        return HTMLEmitter() if self.prefers_html else RichEmitter()

    # Delivery hooks — override as needed
    def warn(self, diag: Diagnostic):
        """Default: integrate with Python warnings and also print to stderr if terminal."""
        category = RAIWarning
        rendered = self.renderer().emit(diag)
        if rendered in self.seen_diagnostics:
            return  # avoid duplicate output
        # If not HTML and we have a TTY, echo the pretty string too
        if not self.prefers_html and sys.stderr and sys.stderr.isatty():
            sys.stderr.write(rendered.rstrip() + "\n")
        # route control via warnings package
        warnings.warn(f"[{diag.name}] {diag.message}", category=category, stacklevel=3)
        self._trace(diag)
        self.seen_diagnostics.add(rendered)


    def err(self, diag: Diagnostic, exception: bool = False):
        """Default: print (or display) and raise DiagnosticException."""
        # Echo before raising for better UX in terminals/CI
        rendered = self.renderer().emit(diag)
        if rendered in self.seen_diagnostics:
            return  # avoid duplicate output
        if self.prefers_html:
            # In notebook-y envs, try to display inline
            try:
                from IPython.display import display, HTML as _HTML
                display(_HTML(rendered))
            except Exception:
                sys.stderr.write("[HTML diagnostic suppressed]\n")
        else:
            sys.stderr.write(rendered.rstrip() + "\n")

        self._trace(diag, error=True)
        self.seen_diagnostics.add(rendered)
        if exception:
            raise RAIException(diag)

    def _trace(self, diag: Diagnostic, error: bool = False):
        try:
            tracer = get_tracer()
            payload = diag.to_dict()
            tracer.add_event("diagnostic", diagnostic=payload)
            if error:
                tracer.set_status(ok=False, message=diag.message)
        except Exception:
            pass

#------------------------------------------------------
# Envs
#------------------------------------------------------

class CI(EnvBase):
    def is_active(self) -> bool:
        return any(os.getenv(k) for k in ("CI", "GITHUB_ACTIONS", "BUILD_NUMBER", "TEAMCITY_VERSION"))

    def warn(self, diag: Diagnostic):
        # keep CI logs plain and controllable via warnings
        rendered = self.renderer().emit(diag)
        warnings.warn(f"[{diag.name}] {diag.message}", category=RAIWarning, stacklevel=3)
        sys.stderr.write(rendered.rstrip() + "\n")
        self._trace(diag)

    def err(self, diag: Diagnostic, exception: bool = False):
        rendered = self.renderer().emit(diag)
        sys.stderr.write(rendered.rstrip() + "\n")
        self._trace(diag)
        if exception:
            raise RAIException(diag)

class Terminal(EnvBase):
    def is_active(self) -> bool:
        try:
            return sys.stderr.isatty()
        except Exception:
            return False

class File(EnvBase):
    """Non-interactive file/script run."""
    def is_active(self) -> bool:
        # If stderr is not a TTY and not a known notebook/colab/hex, treat as file
        return (not sys.stderr.isatty()) and ("ipykernel" not in sys.modules) and ("google.colab" not in sys.modules)

    def warn(self, diag: Diagnostic):
        # just warnings integration (no fancy output)
        warnings.warn(f"[{diag.name}] {diag.message}", category=RAIWarning, stacklevel=3)
        self._trace(diag)

    def err(self, diag: Diagnostic, exception: bool = False):
        self._trace(diag)
        if exception:
            raise RAIException(diag)

class Jupyter(EnvBase):
    prefers_html = True
    def is_active(self) -> bool:
        try:
            from IPython import get_ipython #type: ignore
            ip = get_ipython()
            return bool(ip and ip.__class__.__name__.lower().endswith("zmqinteractiveshell"))
        except Exception:
            return False

class Colab(EnvBase):
    prefers_html = True
    def is_active(self) -> bool:
        return "google.colab" in sys.modules

class Hex(EnvBase):
    prefers_html = True
    def is_active(self) -> bool:
        # Hex notebooks expose 'HEX_RUN' env or similar; keep flexible
        return bool(os.getenv("HEX_RUN") or "hex" in sys.modules)

#------------------------------------------------------
# find env
#------------------------------------------------------

def find_env():
    return more_itertools.first_true(
        [
            CI(),
            Terminal(),
            File(),
            Jupyter(),
            Colab(),
            Hex(),
        ],
        pred=lambda k: k.is_active(),
        default=File(),
    )

ENV = find_env()