import json
import os
import sys

CREW_FILE = "crew.json"
MODULES_DIR = "crew_modules"

def load_crew_file():
    # Attempt to load the config file. Return None if it doesn't exist yet.
    if not os.path.exists(CREW_FILE):
        return None
    try:
        with open(CREW_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {CREW_FILE} is not a valid JSON file.")
        sys.exit(1)

def save_crew_file(data):
    # Dump the dict back to json with pretty printing
    with open(CREW_FILE, "w") as f:
        json.dump(data, f, indent=2)

def create_initial_crew_file(name, version, description, main, author, license):
    # Don't overwrite an existing config, that would be bad.
    if os.path.exists(CREW_FILE):
        print(f"Error: {CREW_FILE} already exists.")
        return False
    
    data = {
        "name": name,
        "version": version,
        "description": description,
        "main": main,
        "scripts": {
            "test": "echo \"Error: no test specified\" && exit 1",
            "build": "gcc main.c -o app"
        },
        "author": author,
        "license": license,
        "dependencies": {}
    }
    save_crew_file(data)
    return True

def ensure_modules_dir():
    # Lazy creation of the modules directory
    if not os.path.exists(MODULES_DIR):
        os.makedirs(MODULES_DIR)

def install_package(url_arg):
    # Support for 'url@tag' syntax to pin versions
    ensure_modules_dir()
    
    if "@" in url_arg:
        url, version = url_arg.split("@", 1)
    else:
        url = url_arg
        version = None # Default to HEAD (default branch)

    package_name = url.split("/")[-1]
    if package_name.endswith(".git"):
        package_name = package_name[:-4]
    
    target_path = os.path.join(MODULES_DIR, package_name)
    
    if os.path.exists(target_path):
        print(f"Package {package_name} is already installed.")
        # TODO: Handle version updates or switching tags if installed version differs
    else:
        print(f"Installing {package_name} from {url}...")
        exit_code = os.system(f"git clone {url} {target_path}")
        if exit_code != 0:
            print(f"Error: Failed to clone {url}")
            return False
    
    # If a tag/branch was specified, detach HEAD to that commit
    if version:
        print(f"Checking out version {version}...")
        cwd = os.getcwd()
        os.chdir(target_path)
        exit_code = os.system(f"git checkout {version}")
        os.chdir(cwd)
        
        if exit_code != 0:
            print(f"Error: Failed to checkout version {version}")
            return False
            
    # Update crew.json
    data = load_crew_file()
    if data:
        if "dependencies" not in data:
            data["dependencies"] = {}
        # Persist the dependency. Keep the @tag if it was provided.
        stored_value = f"{url}@{version}" if version else url
        data["dependencies"][package_name] = stored_value
        save_crew_file(data)
        print(f"Added {package_name} ({version if version else 'HEAD'}) to crew.json")
    return True

def install_all():
    # Iterate through dependencies in crew.json and ensure they are cloned
    data = load_crew_file()
    if not data or "dependencies" not in data:
        print("No dependencies found in crew.json")
        return

    ensure_modules_dir()
    for name, url_entry in data["dependencies"].items():
        if "@" in url_entry:
            url, version = url_entry.split("@", 1)
        else:
            url = url_entry
            version = None

        target_path = os.path.join(MODULES_DIR, name)
        if not os.path.exists(target_path):
            print(f"Installing {name} ({version if version else 'HEAD'})...")
            exit_code = os.system(f"git clone {url} {target_path}")
            if exit_code != 0:
                 print(f"Failed to clone {name}")
                 continue
            if version:
                cwd = os.getcwd()
                os.chdir(target_path)
                os.system(f"git checkout {version}")
                os.chdir(cwd)
        else:
            print(f"{name} already installed.")

def run_script(script_name):
    # Basic script runner. Just proxies to os.system for now.
    data = load_crew_file()
    if not data or "scripts" not in data:
        print("No scripts found in crew.json")
        return False
    
    if script_name not in data["scripts"]:
        print(f"Error: missing script: {script_name}")
        # print available scripts? 
        print("Available scripts:")
        for s in data["scripts"]:
            print(f"  {s}")
        return False
    
    command = data["scripts"][script_name]
    print(f"> {data['name']}@{data['version']} {script_name}")
    print(f"> {command}\n")
    
    exit_code = os.system(command)
    if exit_code != 0:
        print(f"Script failed with exit code {exit_code}")
        return False
    return True

def generate_flags():
    # Walk the modules directory and auto-discover include paths.
    # We look for standard 'include' and 'src' folders.
    if not os.path.exists(MODULES_DIR):
        return ""
    
    flags = []
    for item in os.listdir(MODULES_DIR):
        package_path = os.path.join(MODULES_DIR, item)
        if os.path.isdir(package_path):
            # Add the base directory
            flags.append(f"-I{package_path}")
            # If there's an 'include' folder, add that too (standard practice)
            include_path = os.path.join(package_path, "include")
            if os.path.isdir(include_path):
                 flags.append(f"-I{include_path}")
            # Some libraries put headers in 'src', so let's check there as well
            src_path = os.path.join(package_path, "src")
            if os.path.isdir(src_path):
                 flags.append(f"-I{src_path}")
                 
    return " ".join(flags)

def create_project(project_name, template="c"):
    # Scaffolding for new projects. 
    # Supports C and C++ templates with a basic hello world.
    if os.path.exists(project_name):
        print(f"Error: Directory {project_name} already exists.")
        return False
    
    os.makedirs(project_name)
    
    # Create crew.json
    main_file = "main.cpp" if template == "cpp" else "main.c"
    compiler = "g++" if template == "cpp" else "gcc"
    
    crew_data = {
        "name": project_name,
        "version": "1.0.0",
        "description": "",
        "main": main_file,
        "scripts": {
            "test": "echo \"Error: no test specified\" && exit 1",
            "build": f"{compiler} {main_file} $(crew flags) -o app",
            "start": "./app"
        },
        "author": "",
        "license": "GPL-3.0",
        "dependencies": {
            "json": "https://github.com/nlohmann/json.git" if template == "cpp" else None,
            "stb": "https://github.com/nothings/stb.git" if template == "c" else None
        }
    }
    
    # Clean up None values
    crew_data["dependencies"] = {k: v for k, v in crew_data["dependencies"].items() if v}
    
    with open(os.path.join(project_name, "crew.json"), "w") as f:
        json.dump(crew_data, f, indent=2)
        
    # Create main file
    if template == "cpp":
        content = """#include <iostream>

int main() {
    std::cout << "Hello from Crew C++ Project!" << std::endl;
    return 0;
}
"""
    else:
        content = """#include <stdio.h>

int main() {
    printf("Hello from Crew C Project!\\n");
    return 0;
}
"""
    with open(os.path.join(project_name, main_file), "w") as f:
        f.write(content)
        
    # Create .gitignore
    gitignore = """crew_modules/
app
*.o
"""
    with open(os.path.join(project_name, ".gitignore"), "w") as f:
        f.write(gitignore)
        
    print(f"Created new {template} project in {project_name}/")
    print(f"To get started:\n  cd {project_name}\n  crew install\n  crew run build\n  crew run start")
    return True
