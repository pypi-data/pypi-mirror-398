import json
import csv


def export_results(results, file_path, fmt):
    if fmt == 'json':
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=4)
    elif fmt == 'csv':
        keys = results[0].keys()
        with open(file_path, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)
    elif fmt == 'txt':
        with open(file_path, 'w') as f:
            for r in results:
                f.write(f"{r['platform']}: {r.get('url', 'N/A')} ({r['status']})\n")
