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
| `valve_trials.py` | Generates the public static pages |

Run `python validate_data.py` and `python valve_trials.py site` to validate the catalog and build the website into `site/`. The GitHub Actions workflow runs validation before publishing changes pushed to `main`.

Edit the JSON source files in the repository to update trial records. Review the diff and run validation before publishing. The public site has no trial editor.

`status` describes the card's primary evidence (peer-reviewed publication, posted registry results without a primary paper, or study progress). `registry_results_posted` is a separate flag: a published or terminated study can also have results posted on ClinicalTrials.gov. `related_ncts` lists registrations for overlapping or pooled cohorts without implying that they are the primary paper's registration.

## Editorial review

See [DATA_AUDIT.md](DATA_AUDIT.md) for the latest source audit, corrected records, and remaining review limits. New papers and registry IDs proposed by the discovery scripts require human review when the study identity or cohort is ambiguous. Negative and terminated studies remain visible in the catalog.

The site intentionally includes selected major trials, not every registered valve study. Source records and results can change; verify clinical decisions against the original publication, registry, and current guidelines.
