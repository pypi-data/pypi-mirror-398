# mypy: ignore-errors
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """用于修改pip包tag的hook"""
    def initialize(self, version, build_data) -> None:  # noqa: ANN001
        """修改pip包tag"""
        # 让 Hatch 用“最具体”的 wheel tag（cp313-cp313-win32 / manylinux / macosx...）
        # 注意：只有在你没有手动设置 build_data["tag"] 时才会生效
        build_data["infer_tag"] = True

        # 明确声明不是纯 Python 包（影响 wheel 元数据 / 纯包判断）
        build_data["pure_python"] = False

        # HACK: 临时处理方法，完全更名后将移除
        target = "al_inference_engine"
        dist = (getattr(self.metadata.core, "name", "") or "").strip()
        prefixes = {dist, dist.replace("-", "_")}

        force_include = dict(build_data.get("force_include") or {})

        def rewrite(dst: str) -> str:
            n = str(dst).replace("\\", "/")
            for p in prefixes:
                if p and n.startswith(p + "/"):
                    return f"{target}/" + n[len(p) + 1:]
            return str(dst)

        for src, dst in list(force_include.items()):
            force_include[src] = rewrite(dst)

        build_data["force_include"] = force_include
