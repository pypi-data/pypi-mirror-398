from io import StringIO
from typing import Optional

from v0.relationalai import Config
from v0.relationalai.early_access.dsl.adapters.orm.adapter_qb import ORMAdapterQB
from v0.relationalai.early_access.dsl.adapters.owl.adapter import OwlAdapter
from v0.relationalai.early_access.dsl.ontologies.python_printer import PythonPrinter
from v0.relationalai.early_access.dsl.orm.object_oriented_printer import ObjectOrientedPrinter, \
    ObjectOrientedInterfacePrinter
from v0.relationalai.early_access.dsl.orm.printer import Printer, InterfacePrinter

def orm_to_python_qb(orm_file_path: str, output_file_path: str, enums_enabled: bool=False, pyi_enabled: bool=False,
                     model_name: Optional[str] = None, config: Optional[Config] = None, object_oriented: bool=False,
                     space_indent: bool=False) -> None:
    model = ORMAdapterQB(orm_file_path, model_name, config).model
    model_to_python_qb(model, output_file_path, enums_enabled, pyi_enabled, object_oriented, space_indent)
    if pyi_enabled:
        model_to_python_interface_qb(model, f"{output_file_path}i", enums_enabled, object_oriented,
                                     space_indent)

def owl_to_python(owl_file_path: str, output_file_path: str) -> None:
    model_to_python(OwlAdapter(owl_file_path).model, output_file_path)

def model_to_python(model, output_file_path: str) -> None:
    with StringIO() as s:
        PythonPrinter(s).to_python_string(model)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(s.getvalue())

def model_to_python_qb(model, output_file_path: str, enums_enabled: bool=False, pyi_enabled: bool=False,
                       object_oriented: bool=False, space_indent: bool=False) -> None:
    with StringIO() as s:
        if object_oriented:
            ObjectOrientedPrinter(s, space_indent).to_string(model, enums_enabled, pyi_enabled)
        else:
            Printer(s).to_string(model, enums_enabled, pyi_enabled)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(s.getvalue())

def model_to_python_interface_qb(model, output_file_path: str, enums_enabled: bool=False,
                                 object_oriented: bool=False, space_indent: bool=False) -> None:
    with StringIO() as s:
        if object_oriented:
            ObjectOrientedInterfacePrinter(s, space_indent).to_string(model, enums_enabled)
        else:
            InterfacePrinter(s).to_string(model, enums_enabled)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(s.getvalue())

def orm_to_qb_python_string(orm_file_path: str, enums_enabled: bool=False, pyi_enabled: bool=False,
                            model_name: Optional[str] = None, config: Optional[Config] = None,
                            object_oriented: bool=False) -> str:
    return model_to_qb_python_string(ORMAdapterQB(orm_file_path, model_name, config).model, enums_enabled, pyi_enabled, object_oriented)

def owl_to_python_string(owl_file_path: str) -> str:
    return model_to_python_string(OwlAdapter(owl_file_path).model)

def model_to_python_string(model) -> str:
    with StringIO() as s:
        PythonPrinter(s).to_python_string(model)
        return s.getvalue()

def model_to_qb_python_string(model, enums_enabled: bool=False, pyi_enabled: bool=False, object_oriented: bool=False,
                              space_indent: bool=False) -> str:
    with StringIO() as s:
        if object_oriented:
            ObjectOrientedPrinter(s, space_indent).to_string(model, enums_enabled, pyi_enabled)
        else:
            Printer(s).to_string(model, enums_enabled, pyi_enabled)
        return s.getvalue()

def model_to_python_interface_string(model, enums_enabled: bool=False, object_oriented: bool=False,
                                     space_indent: bool=False) -> str:
    with StringIO() as s:
        if object_oriented:
            ObjectOrientedInterfacePrinter(s, space_indent).to_string(model, enums_enabled)
        else:
            InterfacePrinter(s).to_string(model, enums_enabled)
        return s.getvalue()
