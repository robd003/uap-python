#!/usr/bin/env python
# flake8: noqa
from contextlib import suppress
from os import fspath
from pathlib import Path
from typing import Optional, List, Dict

from setuptools import setup, Command, find_namespace_packages
from setuptools.command.build import build, SubCommand
from setuptools.command.editable_wheel import editable_wheel

import yaml


build.sub_commands.insert(0, ("compile-regexes", None))


class CompileRegexes(Command, SubCommand):
    def initialize_options(self) -> None:
        self.pkg_name: Optional[str] = None

    def finalize_options(self) -> None:
        self.pkg_name = self.distribution.get_name().replace("-", "_")

    def get_source_files(self) -> List[str]:
        return ["uap-core/regexes.yaml"]

    def get_outputs(self) -> List[str]:
        return [f"{self.pkg_name}/_regexes.py"]

    def get_output_mapping(self) -> Dict[str, str]:
        return dict(zip(self.get_source_files(), self.get_outputs()))

    def run(self) -> None:
        # FIXME: check git / submodules?
        """
        work_path = self.work_path
        if not os.path.exists(os.path.join(work_path, ".git")):
            return

        log.info("initializing git submodules")
        check_output(["git", "submodule", "init"], cwd=work_path)
        check_output(["git", "submodule", "update"], cwd=work_path)
        """
        if not self.pkg_name:
            return  # or error?

        yaml_src = Path("uap-core", "regexes.yaml")
        if not yaml_src.is_file():
            raise RuntimeError(
                f"Unable to find regexes.yaml, should be at {yaml_src!r}"
            )

        def write_params(fields):
            # strip trailing None values
            while len(fields) > 1 and fields[-1] is None:
                fields.pop()

            for field in fields:
                fp.write((f"        {field!r},\n").encode())

        with yaml_src.open("rb") as f:
            regexes = yaml.safe_load(f)

        if self.editable_mode:
            dist_dir = Path("src")
        else:
            dist_dir = Path(self.get_finalized_command("bdist_wheel").bdist_dir)

        outdir = dist_dir / self.pkg_name
        outdir.mkdir(parents=True, exist_ok=True)

        dest = outdir / "_regexes.py"

        with dest.open("wb") as fp:
            # fmt: off
            fp.write(b"# -*- coding: utf-8 -*-\n")
            fp.write(b"########################################################\n")
            fp.write(b"# NOTICE: This file is autogenerated from regexes.yaml #\n")
            fp.write(b"########################################################\n")
            fp.write(b"\n")
            fp.write(b"from .user_agent_parser import (\n")
            fp.write(b"    UserAgentParser, DeviceParser, OSParser,\n")
            fp.write(b")\n")
            fp.write(b"\n")
            fp.write(b"__all__ = ('USER_AGENT_PARSERS', 'DEVICE_PARSERS', 'OS_PARSERS')\n")
            fp.write(b"\n")
            fp.write(b"USER_AGENT_PARSERS = [\n")
            for device_parser in regexes["user_agent_parsers"]:
                fp.write(b"    UserAgentParser(\n")
                write_params([
                    device_parser["regex"],
                    device_parser.get("family_replacement"),
                    device_parser.get("v1_replacement"),
                    device_parser.get("v2_replacement"),
                ])
                fp.write(b"    ),\n")
            fp.write(b"]\n")
            fp.write(b"\n")
            fp.write(b"DEVICE_PARSERS = [\n")
            for device_parser in regexes["device_parsers"]:
                fp.write(b"    DeviceParser(\n")
                write_params([
                    device_parser["regex"],
                    device_parser.get("regex_flag"),
                    device_parser.get("device_replacement"),
                    device_parser.get("brand_replacement"),
                    device_parser.get("model_replacement"),
                ])
                fp.write(b"    ),\n")
            fp.write(b"]\n")
            fp.write(b"\n")
            fp.write(b"OS_PARSERS = [\n")
            for device_parser in regexes["os_parsers"]:
                fp.write(b"    OSParser(\n")
                write_params([
                    device_parser["regex"],
                    device_parser.get("os_replacement"),
                    device_parser.get("os_v1_replacement"),
                    device_parser.get("os_v2_replacement"),
                    device_parser.get("os_v3_replacement"),
                    device_parser.get("os_v4_replacement"),
                ])
                fp.write(b"    ),\n")
            fp.write(b"]\n")
            # fmt: on


setup(
    cmdclass={
        "compile-regexes": CompileRegexes,
    }
)
