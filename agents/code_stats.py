import subprocess
import json
from pydantic import BaseModel

# this agent will run the `scc` tool against the codebase
# example output:
"""
$ scc -f json2
{"languageSummary":[{"Name":"Python","Bytes":63969,"CodeBytes":0,"Lines":1481,"Code":1203,"Comment":97,"Blank":181,"Complexity":165,"Count":19,"WeightedComplexity":0,"Files":[],"LineLength":null,"ULOC":0},{"Name":"Markdown","Bytes":28179,"CodeBytes":0,"Lines":572,"Code":437,"Comment":0,"Blank":135,"Complexity":0,"Count":13,"WeightedComplexity":0,"Files":[],"LineLength":null,"ULOC":0}],"estimatedCost":45413.12277070424,"estimatedScheduleMonths":4.247593777328709,"estimatedPeople":0.9498484235463265}
"""
class LanguageSummary(BaseModel):
    name: str
    bytes: int
    codebytes: int
    lines: int
    code: int
    comment: int
    blank: int
    complexity: int
    count: int
    weightedcomplexity: int

class CodeStats(BaseModel):
    language_summary: list[LanguageSummary]
    estimated_cost: float
    estimated_schedule_months: float
    estimated_people: float

class CodeStatsAgent():
    # this agent will be used to get the LOC, COCOMO, and other stats for a given codebase
    def __init__(self, code_path: str):
        self.code_path = code_path

    def run(self) -> CodeStats:
        # run scc using a subprocess and capture the output
        result = subprocess.run(["scc", "-f", "json2", "--avg-wage", "40000", "--exclude-dir", "vendor,node_modules,.git", self.code_path], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"scc failed to run: {result.stderr}")
        parsed_result = json.loads(result.stdout)
        language_summary = []
        for lang in parsed_result["languageSummary"]:
            # convert all the keys to lowercase
            lang = {k.lower(): v for k, v in lang.items()}
            language_summary.append(LanguageSummary(**lang))

        stats = CodeStats(
            language_summary=language_summary,
            estimated_cost=parsed_result["estimatedCost"],
            estimated_schedule_months=parsed_result["estimatedScheduleMonths"],
            estimated_people=parsed_result["estimatedPeople"]
        )
        return stats

if __name__ == "__main__":
    stats = CodeStatsAgent(".").run()
    print(stats)
