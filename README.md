# ValveTrials.org

A static, cardiology-facing reference of selected aortic, mitral, and tricuspid valve trials. Trial cards are editorial summaries linked to the original papers and registries; they are not treatment guidance.

## Data and build

| File | Role |
| --- | --- |
| `trials.json` | Aortic and mitral trial records |
| `trials_tricuspid.json` | Tricuspid trial records |
| `model.py` | Data schema and controlled vocabularies |
| `data.py` | Loads both data files |
| `validate_data.py` | Offline checks for duplicate cards and malformed or missing identifiers |
| `valve_trials.py` | Generates the static pages, including the editor |

Run `python validate_data.py` and `python valve_trials.py site` to validate the catalog and build the website into `site/`. The GitHub Actions workflow runs validation before publishing changes pushed to `main`.

The public editor is generated at `editor.html`. Save an edited trial to the list, then export **both** JSON files and replace the corresponding repository files. The editor preserves fields that are not exposed in its form, including linked papers. Review the JSON diff and run validation before publishing.

## Editorial review

See [DATA_AUDIT.md](DATA_AUDIT.md) for the latest source audit, corrected records, and remaining review limits. New papers and registry IDs proposed by the discovery scripts require human review when the study identity or cohort is ambiguous. Negative and terminated studies remain visible in the catalog.

The site intentionally includes selected major trials, not every registered valve study. Source records and results can change; verify clinical decisions against the original publication, registry, and current guidelines.
