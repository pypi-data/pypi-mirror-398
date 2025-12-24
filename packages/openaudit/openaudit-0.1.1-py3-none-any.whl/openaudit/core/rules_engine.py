import yaml
import re
from pathlib import Path
from typing import List
from .domain import Rule

class RulesEngine:
    def __init__(self, rules_path: str):
        self.rules_path = Path(rules_path)

    def load_rules(self) -> List[Rule]:
        rules = []
        path_obj = self.rules_path
        
        if not path_obj.exists():
            return rules

        files_to_load = []
        if path_obj.is_file():
            files_to_load.append(path_obj)
        else:
            files_to_load.extend(path_obj.glob("**/*.yaml"))
            files_to_load.extend(path_obj.glob("**/*.yml"))
            
        for file_path in files_to_load:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if not data or 'rules' not in data:
                        continue
                    
                    for i, r in enumerate(data['rules']):
                        # Basic ID check
                        if 'id' not in r:
                            print(f"Warning: Rule #{i+1} in {file_path} missing 'id'. Skipping.")
                            continue

                        # Handle missing optional fields
                        if 'remediation' not in r:
                             r['remediation'] = "No remediation provided."
                        if 'category' not in r:
                             r['category'] = "general"
                        if 'confidence' not in r:
                             r['confidence'] = "medium"
                        
                        # Validate regex
                        if 'regex' in r:
                            try:
                                re.compile(r['regex'])
                            except re.error as e:
                                print(f"Error: Invalid regex in rule '{r.get('id', 'unknown')}' in {file_path}: {e}")
                                continue
                             
                        try:
                            rules.append(Rule(**r))
                        except Exception as validation_err:
                            print(f"Error validating rule '{r.get('id')}' in {file_path}: {validation_err}")

            except Exception as e:
                print(f"Error loading rules from {file_path}: {e}")
            
        return rules
            
        return rules
