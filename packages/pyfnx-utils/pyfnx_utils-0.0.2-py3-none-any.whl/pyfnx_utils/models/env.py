from dataclasses import dataclass


@dataclass
class PipCondition:
    platform: list[str] | None = None
    os: list[str] | None = None
    accelerator: list[str] | None = None

    def __post_init__(self) -> None:
        if self.platform is not None:
            if not isinstance(self.platform, list) or not all(
                isinstance(x, str) for x in self.platform
            ):
                raise TypeError("platform must be a list of strings")
        if self.os is not None:
            if not isinstance(self.os, list) or not all(
                isinstance(x, str) for x in self.os
            ):
                raise TypeError("os must be a list of strings")
        if self.accelerator is not None:
            if not isinstance(self.accelerator, list) or not all(
                isinstance(x, str) for x in self.accelerator
            ):
                raise TypeError("acclerator must be a list of strings")


@dataclass
class PipDependency:
    package: str
    extra_pip_args: str | None = None
    condition: PipCondition | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.package, str):
            raise TypeError("package must be a string")
        if self.extra_pip_args is not None and not isinstance(self.extra_pip_args, str):
            raise TypeError("extra_pip_args must be a string")
        if self.condition is not None and not isinstance(self.condition, PipCondition):
            raise TypeError("condition must be a PipCondition instance")


@dataclass
class Python3_CondaPip:
    python_version: str
    build_dependencies: list[str]
    dependencies: list[PipDependency]

    def __post_init__(self) -> None:
        if not isinstance(self.python_version, str):
            raise TypeError("python_version must be a string")
        if not isinstance(self.build_dependencies, list) or not all(
            isinstance(x, str) for x in self.build_dependencies
        ):
            raise TypeError("build_dependencies must be a list of strings")
        if not isinstance(self.dependencies, list) or not all(
            isinstance(x, PipDependency) for x in self.dependencies
        ):
            raise TypeError("dependencies must be a list of PipDependency instances")

    @classmethod
    def from_dict(cls, data: dict) -> "Python3_CondaPip":
        if not isinstance(data, dict):
            raise TypeError("Input must be a dictionary")

        deps = [
            PipDependency(
                package=dep["package"],
                extra_pip_args=dep.get("extra_pip_args"),
                condition=PipCondition(
                    platform=dep.get("condition", {}).get("platform"),
                    os=dep.get("condition", {}).get("os"),
                    accelerator=dep.get("condition", {}).get("accelerator")
                ) if dep.get("condition", None) else None
            )
            for dep in data.get("dependencies", [])
        ]

        return cls(
            python_version=data["python_version"],
            build_dependencies=data["build_dependencies"],
            dependencies=deps
        )
    
    def to_conda(self, env_name = "fnnx_env") -> dict:

        deps = ["python=" + self.python_version] + self.build_dependencies
        pip_deps = []
        
        for dep in self.dependencies:
            pkg = dep.package
            if dep.extra_pip_args:
                pkg += " " + " ".join(dep.extra_pip_args)
            if dep.condition:
                # TODO
                print("Conditions are not currently taken into account")
            pip_deps.append(pkg)
        
        return {
            "name": env_name,
            "channels": ["conda-forge"],
            "dependencies": deps + [{"pip": pip_deps}]
        }