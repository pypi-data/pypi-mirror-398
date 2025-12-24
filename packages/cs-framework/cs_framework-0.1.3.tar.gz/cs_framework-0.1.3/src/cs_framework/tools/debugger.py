import os
from typing import List, Dict, Any
from rdflib import Graph

class LogQueryEngine:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.graph = Graph()
        if os.path.exists(log_file):
            try:
                self.graph.parse(log_file, format="turtle")
            except Exception as e:
                print(f"Error loading log file: {e}")

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a SPARQL query and returns the results as a list of dictionaries.
        """
        try:
            results = self.graph.query(query)
            output = []
            for row in results:
                row_dict = {}
                # row is a ResultRow, which behaves like a tuple/dict
                # We need to map variable names to values
                if hasattr(results, 'vars'):
                    for var in results.vars:
                        val = row[var]
                        if val is not None:
                            row_dict[str(var)] = str(val)
                output.append(row_dict)
            return output
        except Exception as e:
            return [{"error": str(e)}]

    def get_summary(self) -> Dict[str, int]:
        """
        Returns a summary of the log (counts of Concepts, Events, Actions).
        """
        summary = {}
        summary['concepts'] = len(list(self.graph.subjects(predicate=None, object=None))) # Rough count
        # Better to use specific queries
        
        q_concepts = "SELECT (COUNT(?s) as ?count) WHERE { ?s a <http://cs-framework.org/schema#Concept> }"
        q_events = "SELECT (COUNT(?s) as ?count) WHERE { ?s a <http://cs-framework.org/schema#Event> }"
        q_actions = "SELECT (COUNT(?s) as ?count) WHERE { ?s a <http://cs-framework.org/schema#Action> }"
        
        summary['concepts'] = self._get_count(q_concepts)
        summary['events'] = self._get_count(q_events)
        summary['actions'] = self._get_count(q_actions)
        
        return summary

    def _get_count(self, query: str) -> int:
        try:
            res = self.execute_query(query)
            if res and 'count' in res[0]:
                return int(res[0]['count'])
        except:
            pass
        return 0
