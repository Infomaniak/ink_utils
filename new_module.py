import os
from pathlib import Path
from typing import Any

import config
from file_manipulations_utils import find_closest_parent_directory_containing


def new_module(args):
    project_root = config.get_project_module_parent()
    _create_android_module(project_root, args.module_name, args.package_name)


def _create_android_module(parent_path, module_name, package_name):
    module_path = Path(parent_path) / module_name
    src_path = module_path / "src" / "main" / "kotlin" / Path(package_name.replace(".", "/"))

    os.makedirs(src_path, exist_ok=True)

    build_gradle_content = _get_build_gradle_content(package_name)
    example_kt_content = _get_default_kt_file_content(package_name)

    (module_path / "build.gradle.kts").write_text(build_gradle_content, encoding="utf-8")
    (src_path / "Example.kt").write_text(example_kt_content, encoding="utf-8")

    add_include_in_closest_settings_gradle_kts(module_name, module_path, package_name)


def add_include_in_closest_settings_gradle_kts(module_name, module_path: Any, package_name):
    project_name = ":" + module_name.replace("/", ":")
    if "/" in module_name:
        project_name = ":" + ":".join(module_name.split("/")[1:])

    settings_gradle_folder = find_closest_parent_directory_containing(module_path, ["settings.gradle.kts"])
    if settings_gradle_folder is None:
        print(f"No gradle settings found for {package_name}, add `include(\"{project_name}\")` manually")
        raise SystemExit(1)
    else:
        settings_gradle_file = Path(settings_gradle_folder) / "settings.gradle.kts"
        settings_gradle_file_content = settings_gradle_file.read_text(encoding="utf-8")
        updated_content = settings_gradle_file_content + f"\ninclude(\"{project_name}\")"
        settings_gradle_file.write_text(updated_content, encoding="utf-8")


def _get_default_kt_file_content(package_name):
    return f"""
package {package_name}

class Example {{
    
}}
""".strip()


def _get_build_gradle_content(package_name):
    return f"""
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
    
plugins {{
    // TODO: Choose only what's needed
    alias(core.plugins.android.library)
    alias(core.plugins.kotlin.android)
    alias(core.plugins.compose.compiler)
}}

val coreCompileSdk: Int by rootProject.extra
val coreMinSdk: Int by rootProject.extra
val javaVersion: JavaVersion by rootProject.extra

android {{
    namespace = "{package_name}"
    compileSdk = coreCompileSdk

    defaultConfig {{
        minSdk = coreMinSdk
    }}

    compileOptions {{
        sourceCompatibility = javaVersion
        targetCompatibility = javaVersion
    }}

    // TODO: Choose only what's needed
    buildFeatures {{
        compose = true
    }}

    kotlin {{
        compilerOptions {{
            jvmTarget.set(JvmTarget.fromTarget(javaVersion.toString()))
        }}
    }}
}}

dependencies {{
    // TODO: Choose only what's needed
    
    implementation(core.infomaniak.core.ui.compose.margin)

    implementation(platform(core.compose.bom))
    implementation(core.compose.foundation)
    implementation(core.compose.material3)
    implementation(core.compose.ui.android)
    implementation(core.compose.ui.tooling.preview)
    debugImplementation(core.compose.ui.tooling)
}}
""".strip()
