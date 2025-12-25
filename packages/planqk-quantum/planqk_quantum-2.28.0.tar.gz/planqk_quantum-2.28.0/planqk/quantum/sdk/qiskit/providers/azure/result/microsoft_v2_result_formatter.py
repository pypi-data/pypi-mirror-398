import ast
import json
import re
from typing import List, Dict, Any

from qiskit.providers import JobStatus
from qiskit.result.models import ExperimentResult

from planqk.quantum.sdk.qiskit import PlanqkQiskitJob
from planqk.quantum.sdk.qiskit.providers.azure.result.result_formatter import ResultFormatter

MICROSOFT_OUTPUT_DATA_FORMAT_V2 = "microsoft.quantum-results.v2"


class MicrosoftV2ResultFormatter(ResultFormatter):
    """
       Transform the Azure microsoft.quantum-results.v2 results to Qiskit result format.

       Adapted from Azure Quantum Qiskit SDK's job.py module.

       Original source:
       Azure Quantum SDK (MIT License)
       GitHub Repository: https://github.com/microsoft/azure-quantum-python/blob/main/azure-quantum/azure/quantum/qiskit/job.py
    """

    def __init__(self, results: any, job: PlanqkQiskitJob):
        super().__init__(results, job)

    def _get_entry_point_names(self):
        input_params = self.job._job_details.input_params
        # All V2 output is a list of entry points
        entry_points = input_params["items"]
        entry_point_names = []
        for entry_point in entry_points:
            if "entryPoint" not in entry_point:
                raise ValueError("Entry point input_param is missing an 'entryPoint' field")
            entry_point_names.append(entry_point["entryPoint"])
        return entry_point_names if len(entry_point_names) > 0 else ["main"]

    def format_result(self) -> List[Dict[str, Any]]:

        entry_point_names = self._get_entry_point_names()

        results = self._translate_microsoft_v2_results()

        if len(results) != len(entry_point_names):
            raise ValueError("The number of experiment results does not match the number of entry point names")

        headers = self._get_headers()

        if len(results) != len(headers):
            raise ValueError("The number of experiment results does not match the number of headers")

        formatted_results = [{
            "data": result,
            "success": True,
            "shots": self.job.shots,
            "name": name,
            "status": JobStatus.DONE.name,
            "header": header
        } for name, (total_count, result), header in zip(entry_point_names, results, headers)]

        # Currently we just support single experiment jobs
        return ExperimentResult.from_dict(formatted_results[0])

    def _translate_microsoft_v2_results(self):
        """ Translate Microsoft's batching job results histograms into a format that can be consumed by qiskit libraries. """
        az_result_histogram = self._get_results_histogram()
        az_result_shots = self._get_results_shots()

        # If it is a non-batched result, format to be in batch format so we can have one code path
        if isinstance(az_result_histogram, dict):
            az_result_histogram = [az_result_histogram]
            az_result_shots = [az_result_shots]

        histograms = []

        for (histogram, shots) in zip(az_result_histogram, az_result_shots):
            counts = {}
            probabilities = {}

            total_count = len(shots)

            for (display, result) in histogram.items():
                bitstring = MicrosoftV2ResultFormatter._qir_to_qiskit_bitstring(display)
                count = result["count"]
                probability = count / total_count
                counts[bitstring] = count
                probabilities[bitstring] = probability

            formatted_shots = [MicrosoftV2ResultFormatter._qir_to_qiskit_bitstring(shot) for shot in shots]

            histograms.append((total_count, {"counts": counts, "probabilities": probabilities, "memory": formatted_shots}))
        return histograms

    def _get_results_histogram(self) -> List[Dict[str, Any]]:
        results = self.results
        self._validate_results(results)

        results = results["Results"]

        if len(results) == 1:
            results = results[0]
            if "Histogram" not in results:
                raise ValueError(
                    f"\"Histogram\" array was expected to be in the Job results for \"{MICROSOFT_OUTPUT_DATA_FORMAT_V2}\" output format.")

            histogram_values = results["Histogram"]
            outcome_keys = self._process_outcome(histogram_values)

            # Re-mapping object {'Histogram': [{"Outcome": [0], "Display": '[0]', "Count": 500}, {"Outcome": [1], "Display": '[1]', "Count": 500}]} to {'[0]': {"Outcome": [0], "Count": 500}, '[1]': {"Outcome": [1], "Count": 500}}
            return {hist_val["Display"]: {"outcome": outcome, "count": hist_val["Count"]} for outcome, hist_val in
                    zip(outcome_keys, histogram_values)}

        else:
            # Currently not supported: handling the BatchResults edge case
            results_array = []
            for i, result in enumerate(results):
                if "Histogram" not in result:
                    raise ValueError(
                        f"\"Histogram\" array was expected to be in the Job results for result {i} for \"{MICROSOFT_OUTPUT_DATA_FORMAT_V2}\" output format.")

                histogram_values = result["Histogram"]
                outcome_keys = self._process_outcome(histogram_values)

                # Re-mapping object {'Histogram': [{"Outcome": [0], "Display": '[0]', "Count": 500}, {"Outcome": [1], "Display": '[1]', "Count": 500}]} to {'[0]': {"Outcome": [0], "Count": 500}, '[1]': {"Outcome": [1], "Count": 500}}
                results_array.append({hist_val["Display"]: {"outcome": outcome, "count": hist_val["Count"]} for outcome, hist_val in
                                      zip(outcome_keys, histogram_values)})

            return results_array

    def _validate_results(self, results):
        if "DataFormat" not in results or results["DataFormat"] != MICROSOFT_OUTPUT_DATA_FORMAT_V2:
            raise ValueError(
                f"\"DataFormat\" was expected to be \"microsoft.quantum-results.v2\" in the Job results for \"{MICROSOFT_OUTPUT_DATA_FORMAT_V2}\" output format.")
        if "Results" not in results:
            raise ValueError(f"\"Results\" field was expected to be in the Job results for \"{MICROSOFT_OUTPUT_DATA_FORMAT_V2}\" output format.")
        if len(results["Results"]) != 1:
            raise ValueError("\"Results\" array was expected to contain one item as currently only single experiment jobs are supported.")

    def _get_results_shots(self):
        results = self.results
        self._validate_results(results)

        results = results["Results"]

        if len(results) == 1:
            result = results[0]
            if "Shots" not in result:
                raise ValueError(
                    f"\"Shots\" array was expected to be in the Job results for \"{self.details.output_data_format}\" output format.")

            return [self._convert_tuples(shot) for shot in result["Shots"]]
        else:
            # This is handling the BatchResults edge case
            shots_array = []
            for i, result in enumerate(results):
                if "Shots" not in result:
                    raise ValueError(
                        f"\"Shots\" array was expected to be in the Job results for result {i} of \"{self.details.output_data_format}\" output format.")
                shots_array.append([self._convert_tuples(shot) for shot in result["Shots"]])

            return shots_array

    def _process_outcome(self, histogram_results):
        return [self._convert_tuples(v['Outcome']) for v in histogram_results]

    def _convert_tuples(self, data):
        if isinstance(data, dict):
            # Check if the dictionary represents a tuple
            if all(isinstance(k, str) and k.startswith("Item") for k in data.keys()):
                # Convert the dictionary to a tuple
                return tuple(self._convert_tuples(data[f"Item{i + 1}"]) for i in range(len(data)))
            else:
                raise ValueError("Malformed tuple output")
        elif isinstance(data, list):
            # Recursively process list elements
            return [self._convert_tuples(item) for item in data]
        else:
            # Return the data as is (int, string, etc.)
            return data

    @staticmethod
    def _qir_to_qiskit_bitstring(obj):
        """Convert the data structure from Azure into the "schema" used by Qiskit"""
        if isinstance(obj, str) and not re.match(r"[\d\s]+$", obj):
            obj = ast.literal_eval(obj)

        if isinstance(obj, tuple):
            # the outermost implied container is a tuple, and each item is
            # associated with a classical register.
            return " ".join(
                [
                    MicrosoftV2ResultFormatter._qir_to_qiskit_bitstring(term)
                    for term in obj
                ]
            )
        elif isinstance(obj, list):
            # a list is for an individual classical register
            return "".join([str(bit) for bit in obj])
        else:
            return str(obj)

    def _get_headers(self):
        headers = self.job._job_details.input_params
        if (not isinstance(headers, list)):
            headers = [headers]

        # This function will attempt to parse the header into a JSON object, and if the header is not a JSON object, we return the header itself
        def try_parse_json(header):
            try:
                json_object = json.loads(header)
            except (ValueError, TypeError):
                return header
            return json_object

        for header in headers:
            header.pop('qiskit', None)
            for key in header.keys():
                header[key] = try_parse_json(header[key])
        return headers
