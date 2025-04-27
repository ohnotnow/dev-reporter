from pydantic import BaseModel
import subprocess
import json
import sys
from typing import Optional

class ComposerSecurityAdvisory(BaseModel):
    advisoryId: str
    title: str
    cve: Optional[str]
    link: Optional[str]
    severity: str

class ComposerPackageStats(BaseModel):
    name: str
    description: Optional[str]
    installed_version: str
    latest_version: str
    license: str
    security_advisories: list[ComposerSecurityAdvisory]

class ComposerStats(BaseModel):
    packages: list[ComposerPackageStats]

class ComposerStatsAgent():
    def __init__(self, code_path: str):
        self.code_path = code_path

    def run(self) -> ComposerStats:
        # run composer audit --format=json --locked --no-dev
        # run composer show --latest --format=json --locked --no-dev
        # run composer licenses --no-dev --format=json
        # parse the output
        # return the stats
        # we need to run composer install first to get the licenses - otherwise it's not in the output
        result = self.run_composer_install(self.code_path)
        audit_json = self.run_composer_command(["composer", "audit", "--format=json", "--locked", "--no-dev"], self.code_path)
        show_json = self.run_composer_command(["composer", "show", "--latest", "--format=json", "--locked", "--no-dev"], self.code_path)
        licenses_json = self.run_composer_command(["composer", "licenses", "--no-dev", "--format=json"], self.code_path)

        packages = []
        for pkg in show_json.get("locked", []):
            advisories = []
            advisories_data = audit_json.get("advisories", {}).get(pkg['name'], [])
            # sometimes the advisories are a dict, sometimes a list - thanks php/composer json_encode!
            if isinstance(advisories_data, dict):
                advisories_list = list(advisories_data.values())
            elif isinstance(advisories_data, list):
                advisories_list = advisories_data
            else:
                advisories_list = []

            for adv in advisories_list:
                advisories.append(ComposerSecurityAdvisory(**adv))

            packages.append(ComposerPackageStats(
                name=pkg["name"],
                description=pkg.get("description", ""),
                installed_version=pkg["version"],
                latest_version=pkg["latest"],
                license=", ".join(licenses_json.get("dependencies", {}).get(pkg["name"], {}).get("license", [])),
                security_advisories=advisories
            ))

        return ComposerStats(packages=packages)

    def run_composer_command(self, args, cwd):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
        if result.stderr:
            raise RuntimeError(f"Composer command failed: {' '.join(args)}\n{result.stderr}\n{result.stdout}")
        return json.loads(result.stdout)

    def run_composer_install(self, cwd):
        result = subprocess.run(["composer", "install"], cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Composer install failed: {result.stderr}\n{result.stdout}")
        return 0

if __name__ == "__main__":
    agent = ComposerStatsAgent(sys.argv[1])
    stats = agent.run()
    print(stats)
