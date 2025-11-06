import os
from pathlib import Path

import config


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


def _get_default_kt_file_content(package_name):
    return f"""
package {package_name}

class Example {{
    
}}
""".strip()


def _get_build_gradle_content(package_name):
    return f"""
plugins {{
    // TODO: Choose only what's needed
    id("com.android.library")
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

    kotlinOptions {{
        jvmTarget = javaVersion.toString()
    }}
}}

dependencies {{
    // TODO: Choose only what's needed
    implementation(platform(core.compose.bom))
    implementation(core.compose.ui)
}}
""".strip()
