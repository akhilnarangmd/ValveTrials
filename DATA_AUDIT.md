# Trial source audit — 11 October 2026

This audit covers every public card in the current catalog. The registry and bibliographic checks used the ClinicalTrials.gov v2 API and NCBI PubMed E-utilities. The table below provides direct links so each entry can be reviewed against its source.

**Scope:** 103 cards; 86 distinct ClinicalTrials.gov IDs; 403 distinct PubMed IDs resolved. Statuses: ongoing 16, published 81, results posted 4, terminated 1, withdrawn 1.

## What was checked

- Every stored NCT ID resolves to a registry record. Every stored PMID resolves in PubMed. Stored DOI values were compared with their PubMed records.
- Acronyms and URL slugs are unique; the data validator rejects missing identity fields, invalid status/category values, malformed identifiers, duplicate follow-up PMIDs in a card, and a paper reused as another card’s primary.
- We reviewed and corrected conspicuous cohort/identifier mismatches, removed unrelated citations and duplicate cards, and added available registry results to cards that had been marked pending.
- Shared NCT IDs can represent distinct, named cohorts (for example PARTNER 1A and 1B). Shared follow-up papers can cover multiple cohorts; they are not separate trial cards.

## Limits and remaining editorial review

- Identifier resolution does **not** prove every endpoint, number, guideline statement, or narrative claim in a card. A clinician should compare each result sentence against the linked source before production release, especially studies with multiple cohorts or evolving follow-up.
- PARTNER 2 ViV uses dedicated registry NCT03225001, while its 2017 primary paper declares the parent PARTNER II registration NCT01314313. The card now states this relationship explicitly; the populations should not be treated as identical.
- Registry results are labeled separately from peer-reviewed primary results. Planned enrollment counts are marked “planned”; posted outcome denominators are stated on the relevant cards.

## Card-by-card source index

| Trial | Valve | Status | Registry | Primary paper | Source check |
| --- | --- | --- | --- | --- | --- |
| PARTNER 1B | Aortic | published | [NCT00530894](https://clinicaltrials.gov/study/NCT00530894) | [PMID 20961243](https://pubmed.ncbi.nlm.nih.gov/20961243/) | IDs/DOIs resolved |
| PARTNER 1A | Aortic | published | [NCT00530894](https://clinicaltrials.gov/study/NCT00530894) | [PMID 21639811](https://pubmed.ncbi.nlm.nih.gov/21639811/) | IDs/DOIs resolved |
| CoreValve Extreme Risk | Aortic | published | [NCT01240902](https://clinicaltrials.gov/study/NCT01240902) | [PMID 24657695](https://pubmed.ncbi.nlm.nih.gov/24657695/) | IDs/DOIs resolved |
| CoreValve High Risk | Aortic | published | [NCT01240902](https://clinicaltrials.gov/study/NCT01240902) | [PMID 24678937](https://pubmed.ncbi.nlm.nih.gov/24678937/) | IDs/DOIs resolved |
| PARTNER 2A | Aortic | published | [NCT01314313](https://clinicaltrials.gov/study/NCT01314313) | [PMID 27040324](https://pubmed.ncbi.nlm.nih.gov/27040324/) | IDs/DOIs resolved |
| SURTAVI | Aortic | published | [NCT01586910](https://clinicaltrials.gov/study/NCT01586910) | [PMID 28304219](https://pubmed.ncbi.nlm.nih.gov/28304219/) | IDs/DOIs resolved |
| UK TAVI | Aortic | published | [ISRCTN57819173](https://www.isrctn.com/ISRCTN57819173) | [PMID 35579641](https://pubmed.ncbi.nlm.nih.gov/35579641/) | IDs/DOIs resolved |
| PARTNER 3 | Aortic | published | [NCT02675114](https://clinicaltrials.gov/study/NCT02675114) | [PMID 30883058](https://pubmed.ncbi.nlm.nih.gov/30883058/) | IDs/DOIs resolved |
| Evolut Low Risk | Aortic | published | [NCT02701283](https://clinicaltrials.gov/study/NCT02701283) | [PMID 30883053](https://pubmed.ncbi.nlm.nih.gov/30883053/) | IDs/DOIs resolved |
| NOTION | Aortic | published | [NCT01057173](https://clinicaltrials.gov/study/NCT01057173) | [PMID 30704298](https://pubmed.ncbi.nlm.nih.gov/30704298/) | IDs/DOIs resolved |
| NOTION-2 | Aortic | published | [NCT02825134](https://clinicaltrials.gov/study/NCT02825134) | [PMID 38747246](https://pubmed.ncbi.nlm.nih.gov/38747246/) | IDs/DOIs resolved |
| DEDICATE-DZHK6 | Aortic | published | [NCT03112980](https://clinicaltrials.gov/study/NCT03112980) | [PMID 38588025](https://pubmed.ncbi.nlm.nih.gov/38588025/) | IDs/DOIs resolved |
| CHOICE | Aortic | published | [NCT01645202](https://clinicaltrials.gov/study/NCT01645202) | [PMID 24682026](https://pubmed.ncbi.nlm.nih.gov/24682026/) | IDs/DOIs resolved |
| REPRISE III | Aortic | published | [NCT02202434](https://clinicaltrials.gov/study/NCT02202434) | [PMID 29297076](https://pubmed.ncbi.nlm.nih.gov/29297076/) | IDs/DOIs resolved |
| Portico IDE | Aortic | published | [NCT02000115](https://clinicaltrials.gov/study/NCT02000115) | [PMID 32593323](https://pubmed.ncbi.nlm.nih.gov/32593323/) | IDs/DOIs resolved |
| SCOPE I | Aortic | published | [NCT03011346](https://clinicaltrials.gov/study/NCT03011346) | [PMID 31570258](https://pubmed.ncbi.nlm.nih.gov/31570258/) | IDs/DOIs resolved |
| SCOPE II | Aortic | published | [NCT03192813](https://clinicaltrials.gov/study/NCT03192813) | [PMID 33054367](https://pubmed.ncbi.nlm.nih.gov/33054367/) | IDs/DOIs resolved |
| SOLVE-TAVI | Aortic | published | [NCT02737150](https://clinicaltrials.gov/study/NCT02737150) | [PMID 32049283](https://pubmed.ncbi.nlm.nih.gov/32049283/) | IDs/DOIs resolved |
| SMART | Aortic | published | [NCT04722250](https://clinicaltrials.gov/study/NCT04722250) | [PMID 38587261](https://pubmed.ncbi.nlm.nih.gov/38587261/) | IDs/DOIs resolved |
| LANDMARK | Aortic | published | [NCT04275726](https://clinicaltrials.gov/study/NCT04275726) | [PMID 38795719](https://pubmed.ncbi.nlm.nih.gov/38795719/) | IDs/DOIs resolved |
| ACURATE IDE | Aortic | published | [NCT03735667](https://clinicaltrials.gov/study/NCT03735667) | [PMID 40412426](https://pubmed.ncbi.nlm.nih.gov/40412426/) | IDs/DOIs resolved |
| REPRISE I | Aortic | published | [NCT01383720](https://clinicaltrials.gov/study/NCT01383720) | [PMID 24169077](https://pubmed.ncbi.nlm.nih.gov/24169077/) | IDs/DOIs resolved |
| REPRISE II | Aortic | published | [NCT01627691](https://clinicaltrials.gov/study/NCT01627691) | [PMID 26892084](https://pubmed.ncbi.nlm.nih.gov/26892084/) | IDs/DOIs resolved |
| EARLY TAVR | Aortic | published | [NCT03042104](https://clinicaltrials.gov/study/NCT03042104) | [PMID 39466903](https://pubmed.ncbi.nlm.nih.gov/39466903/) | IDs/DOIs resolved |
| EVOLVED | Aortic | published | [NCT03094143](https://clinicaltrials.gov/study/NCT03094143) | [PMID 39466640](https://pubmed.ncbi.nlm.nih.gov/39466640/) | IDs/DOIs resolved |
| AVATAR | Aortic | published | [NCT02436655](https://clinicaltrials.gov/study/NCT02436655) | [PMID 34779220](https://pubmed.ncbi.nlm.nih.gov/34779220/) | IDs/DOIs resolved |
| TAVR UNLOAD | Aortic | published | [NCT02661451](https://clinicaltrials.gov/study/NCT02661451) | [PMID 39480381](https://pubmed.ncbi.nlm.nih.gov/39480381/) | IDs/DOIs resolved |
| PARTNER 2 ViV | Aortic | published | [NCT03225001](https://clinicaltrials.gov/study/NCT03225001) | [PMID 28473128](https://pubmed.ncbi.nlm.nih.gov/28473128/) | Parent/subregistry caveat |
| REDO-TAVR | Aortic | published | — | [PMID 32327098](https://pubmed.ncbi.nlm.nih.gov/32327098/) | IDs/DOIs resolved |
| VIVID | Aortic | published | — | [PMID 25005653](https://pubmed.ncbi.nlm.nih.gov/25005653/) | IDs/DOIs resolved |
| PARTNER 3 Bicuspid | Aortic | published | [NCT02675114](https://clinicaltrials.gov/study/NCT02675114) | [PMID 35272777](https://pubmed.ncbi.nlm.nih.gov/35272777/) | IDs/DOIs resolved |
| Evolut Bicuspid | Aortic | published | [NCT03635424](https://clinicaltrials.gov/study/NCT03635424) | [PMID 39048253](https://pubmed.ncbi.nlm.nih.gov/39048253/) | IDs/DOIs resolved |
| LRT Bicuspid | Aortic | published | [NCT02628899](https://clinicaltrials.gov/study/NCT02628899) | [PMID 32381181](https://pubmed.ncbi.nlm.nih.gov/32381181/) | IDs/DOIs resolved |
| ALIGN-AR | Aortic | published | [NCT04415047](https://clinicaltrials.gov/study/NCT04415047) | [PMID 38552656](https://pubmed.ncbi.nlm.nih.gov/38552656/) | IDs/DOIs resolved |
| J-Valve JOURNEY | Aortic | ongoing | [NCT06455787](https://clinicaltrials.gov/study/NCT06455787) | — | IDs/DOIs resolved |
| J-Valve EFS | Aortic | ongoing | [NCT06034028](https://clinicaltrials.gov/study/NCT06034028) | — | IDs/DOIs resolved |
| Trilogy vs SAVR (US IDE) | Aortic | ongoing | [NCT06608823](https://clinicaltrials.gov/study/NCT06608823) | — | IDs/DOIs resolved |
| Hydra CE | Aortic | published | [NCT02434263](https://clinicaltrials.gov/study/NCT02434263) | [PMID 34991828](https://pubmed.ncbi.nlm.nih.gov/34991828/) | IDs/DOIs resolved |
| Navitor Global | Aortic | ongoing | — | — | IDs/DOIs resolved |
| VANTAGE | Aortic | results posted | [NCT04788888](https://clinicaltrials.gov/study/NCT04788888) | — | IDs/DOIs resolved |
| ENVISION IDE | Aortic | ongoing | [NCT05932615](https://clinicaltrials.gov/study/NCT05932615) | — | IDs/DOIs resolved |
| DurAVR PARADIGM | Aortic | ongoing | [NCT05712161](https://clinicaltrials.gov/study/NCT05712161) | — | IDs/DOIs resolved |
| Cardioband CE | Mitral | published | [NCT01841554](https://clinicaltrials.gov/study/NCT01841554) | [PMID 30124798](https://pubmed.ncbi.nlm.nih.gov/30124798/) | IDs/DOIs resolved |
| ACTIVE | Mitral | terminated | [NCT03016975](https://clinicaltrials.gov/study/NCT03016975) | — | IDs/DOIs resolved |
| Mitralign | Mitral | published | [NCT01852149](https://clinicaltrials.gov/study/NCT01852149) | [PMID 27339489](https://pubmed.ncbi.nlm.nih.gov/27339489/) | IDs/DOIs resolved |
| REDUCE-FMR | Mitral | published | [NCT02325830](https://clinicaltrials.gov/study/NCT02325830) | [PMID 31521683](https://pubmed.ncbi.nlm.nih.gov/31521683/) | IDs/DOIs resolved |
| EMPOWER | Mitral | ongoing | [NCT03142152](https://clinicaltrials.gov/study/NCT03142152) | — | IDs/DOIs resolved |
| EVEREST II | Mitral | published | [NCT00209274](https://clinicaltrials.gov/study/NCT00209274) | [PMID 21463154](https://pubmed.ncbi.nlm.nih.gov/21463154/) | IDs/DOIs resolved |
| EVEREST II HRS | Mitral | published | [NCT00209274](https://clinicaltrials.gov/study/NCT00209274) | [PMID 25011722](https://pubmed.ncbi.nlm.nih.gov/25011722/) | IDs/DOIs resolved |
| PASCAL CLASP | Mitral | published | [NCT03170349](https://clinicaltrials.gov/study/NCT03170349) | [PMID 31255562](https://pubmed.ncbi.nlm.nih.gov/31255562/) | IDs/DOIs resolved |
| CLASP IID | Mitral | published | [NCT03706833](https://clinicaltrials.gov/study/NCT03706833) | [PMID 36121247](https://pubmed.ncbi.nlm.nih.gov/36121247/) | IDs/DOIs resolved |
| REPAIR MR | Mitral | ongoing | [NCT04198870](https://clinicaltrials.gov/study/NCT04198870) | — | IDs/DOIs resolved |
| COAPT | Mitral | published | [NCT01626079](https://clinicaltrials.gov/study/NCT01626079) | [PMID 30280640](https://pubmed.ncbi.nlm.nih.gov/30280640/) | IDs/DOIs resolved |
| MITRA-FR | Mitral | published | [NCT01920698](https://clinicaltrials.gov/study/NCT01920698) | [PMID 30145927](https://pubmed.ncbi.nlm.nih.gov/30145927/) | IDs/DOIs resolved |
| RESHAPE-HF2 | Mitral | published | [NCT02444338](https://clinicaltrials.gov/study/NCT02444338) | [PMID 39216092](https://pubmed.ncbi.nlm.nih.gov/39216092/) | IDs/DOIs resolved |
| MATTERHORN | Mitral | published | [NCT02371512](https://clinicaltrials.gov/study/NCT02371512) | [PMID 39216093](https://pubmed.ncbi.nlm.nih.gov/39216093/) | IDs/DOIs resolved |
| CLASP IIF | Mitral | published | [NCT03706833](https://clinicaltrials.gov/study/NCT03706833) | [PMID 42233921](https://pubmed.ncbi.nlm.nih.gov/42233921/) | IDs/DOIs resolved |
| TACT (NeoChord) | Mitral | published | [NCT01777815](https://clinicaltrials.gov/study/NCT01777815) | [PMID 24076529](https://pubmed.ncbi.nlm.nih.gov/24076529/) | IDs/DOIs resolved |
| NeoChord Registry | Mitral | results posted | [NCT01784055](https://clinicaltrials.gov/study/NCT01784055) | — | IDs/DOIs resolved |
| ReChord | Mitral | withdrawn | [NCT02829749](https://clinicaltrials.gov/study/NCT02829749) | — | IDs/DOIs resolved |
| HARPOON TRACER | Mitral | published | [NCT02768870](https://clinicaltrials.gov/study/NCT02768870) | [PMID 29102688](https://pubmed.ncbi.nlm.nih.gov/29102688/) | IDs/DOIs resolved |
| RESTORE (Harpoon) | Mitral | ongoing | [NCT04375332](https://clinicaltrials.gov/study/NCT04375332) | — | IDs/DOIs resolved |
| Tendyne Feasibility | Mitral | published | [NCT02321514](https://clinicaltrials.gov/study/NCT02321514) | [PMID 28040318](https://pubmed.ncbi.nlm.nih.gov/28040318/) | IDs/DOIs resolved |
| Tendyne Expanded | Mitral | published | [NCT02321514](https://clinicaltrials.gov/study/NCT02321514) | [PMID 34736561](https://pubmed.ncbi.nlm.nih.gov/34736561/) | IDs/DOIs resolved |
| SUMMIT | Mitral | published | [NCT03433274](https://clinicaltrials.gov/study/NCT03433274) | [PMID 41194751](https://pubmed.ncbi.nlm.nih.gov/41194751/) | IDs/DOIs resolved |
| Intrepid Pilot | Mitral | published | [NCT02322840](https://clinicaltrials.gov/study/NCT02322840) | [PMID 29102689](https://pubmed.ncbi.nlm.nih.gov/29102689/) | IDs/DOIs resolved |
| Intrepid TA (2-yr) | Mitral | published | [NCT02322840](https://clinicaltrials.gov/study/NCT02322840) | [PMID 38639690](https://pubmed.ncbi.nlm.nih.gov/38639690/) | IDs/DOIs resolved |
| Intrepid TS-EFS | Mitral | published | — | [PMID 34747699](https://pubmed.ncbi.nlm.nih.gov/34747699/) | IDs/DOIs resolved |
| APOLLO | Mitral | published | [NCT03242642](https://clinicaltrials.gov/study/NCT03242642) | [PMID 41251714](https://pubmed.ncbi.nlm.nih.gov/41251714/) | IDs/DOIs resolved |
| APOLLO-EU | Mitral | ongoing | [NCT05496998](https://clinicaltrials.gov/study/NCT05496998) | — | IDs/DOIs resolved |
| SAPIEN M3 FIH | Mitral | published | — | [PMID 30898198](https://pubmed.ncbi.nlm.nih.gov/30898198/) | IDs/DOIs resolved |
| ENCIRCLE | Mitral | published | [NCT04153292](https://clinicaltrials.gov/study/NCT04153292) | [PMID 41167201](https://pubmed.ncbi.nlm.nih.gov/41167201/) | IDs/DOIs resolved |
| HighLife TSMVR | Mitral | published | [NCT04029363](https://clinicaltrials.gov/study/NCT04029363) | [PMID 37999708](https://pubmed.ncbi.nlm.nih.gov/37999708/) | IDs/DOIs resolved |
| Tiara EFS | Mitral | results posted | [NCT02276547](https://clinicaltrials.gov/study/NCT02276547) | — | IDs/DOIs resolved |
| Cephea FIH | Mitral | published | [NCT03988946](https://clinicaltrials.gov/study/NCT03988946) | [PMID 31510775](https://pubmed.ncbi.nlm.nih.gov/31510775/) | IDs/DOIs resolved |
| Cephea EFS | Mitral | ongoing | [NCT05061004](https://clinicaltrials.gov/study/NCT05061004) | — | IDs/DOIs resolved |
| AltaValve EFS | Mitral | published | — | [PMID 41224388](https://pubmed.ncbi.nlm.nih.gov/41224388/) | IDs/DOIs resolved |
| AltaValve Pivotal | Mitral | ongoing | [NCT06465745](https://clinicaltrials.gov/study/NCT06465745) | — | IDs/DOIs resolved |
| EVOQUE Eos MISCEND | Mitral | ongoing | [NCT02718001](https://clinicaltrials.gov/study/NCT02718001) | — | IDs/DOIs resolved |
| MITRAL | Mitral | published | [NCT02370511](https://clinicaltrials.gov/study/NCT02370511) | [PMID 33888230](https://pubmed.ncbi.nlm.nih.gov/33888230/) | IDs/DOIs resolved |
| PARTNER 3 MVIV | Mitral | published | [NCT03193801](https://clinicaltrials.gov/study/NCT03193801) | [PMID 39034924](https://pubmed.ncbi.nlm.nih.gov/39034924/) | IDs/DOIs resolved |
| SAPIEN 3 MViV Registry | Mitral | published | — | [PMID 32745164](https://pubmed.ncbi.nlm.nih.gov/32745164/) | IDs/DOIs resolved |
| MITRAL II | Mitral | ongoing | [NCT04408430](https://clinicaltrials.gov/study/NCT04408430) | — | IDs/DOIs resolved |
| LAMPOON IDE | Mitral | published | [NCT03015194](https://clinicaltrials.gov/study/NCT03015194) | [PMID 31118146](https://pubmed.ncbi.nlm.nih.gov/31118146/) | IDs/DOIs resolved |
| PARTNER II S3i | Aortic | published | [NCT03222128](https://clinicaltrials.gov/study/NCT03222128) | [PMID 27053442](https://pubmed.ncbi.nlm.nih.gov/27053442/) | IDs/DOIs resolved |
| TRILUMINATE | Tricuspid | published | [NCT03227757](https://clinicaltrials.gov/study/NCT03227757) | [PMID 31708188](https://pubmed.ncbi.nlm.nih.gov/31708188/) | IDs/DOIs resolved |
| TRILUMINATE Pivotal | Tricuspid | published | [NCT03904147](https://clinicaltrials.gov/study/NCT03904147) | [PMID 36876753](https://pubmed.ncbi.nlm.nih.gov/36876753/) | IDs/DOIs resolved |
| TRI-FR | Tricuspid | published | [NCT04646811](https://clinicaltrials.gov/study/NCT04646811) | [PMID 39602173](https://pubmed.ncbi.nlm.nih.gov/39602173/) | IDs/DOIs resolved |
| bRIGHT | Tricuspid | published | [NCT04483089](https://clinicaltrials.gov/study/NCT04483089) | [PMID 38759905](https://pubmed.ncbi.nlm.nih.gov/38759905/) | IDs/DOIs resolved |
| CLASP TR EFS | Tricuspid | published | [NCT03745313](https://clinicaltrials.gov/study/NCT03745313) | [PMID 37137586](https://pubmed.ncbi.nlm.nih.gov/37137586/) | IDs/DOIs resolved |
| CLASP II TR | Tricuspid | ongoing | [NCT04097145](https://clinicaltrials.gov/study/NCT04097145) | — | IDs/DOIs resolved |
| TRISCEND II | Tricuspid | published | [NCT04482062](https://clinicaltrials.gov/study/NCT04482062) | [PMID 39475399](https://pubmed.ncbi.nlm.nih.gov/39475399/) | IDs/DOIs resolved |
| LuX-Valve | Tricuspid | published | [NCT04436653](https://clinicaltrials.gov/study/NCT04436653) | [PMID 40208152](https://pubmed.ncbi.nlm.nih.gov/40208152/) | IDs/DOIs resolved |
| TRI-REPAIR | Tricuspid | published | [NCT02981953](https://clinicaltrials.gov/study/NCT02981953) | [PMID 30999993](https://pubmed.ncbi.nlm.nih.gov/30999993/) | IDs/DOIs resolved |
| SCOUT | Tricuspid | published | [NCT02574650](https://clinicaltrials.gov/study/NCT02574650) | [PMID 28385308](https://pubmed.ncbi.nlm.nih.gov/28385308/) | IDs/DOIs resolved |
| TRICUS EURO | Tricuspid | published | [NCT04141137](https://clinicaltrials.gov/study/NCT04141137) | [PMID 35583363](https://pubmed.ncbi.nlm.nih.gov/35583363/) | IDs/DOIs resolved |
| HOVER | Tricuspid | results posted | [NCT02339974](https://clinicaltrials.gov/study/NCT02339974) | — | IDs/DOIs resolved |
| TANDEM I (CroíValve) | Tricuspid | ongoing | [NCT05296148](https://clinicaltrials.gov/study/NCT05296148) | — | IDs/DOIs resolved |
| MitraClip in TR (early) | Tricuspid | published | — | [PMID 28336788](https://pubmed.ncbi.nlm.nih.gov/28336788/) | IDs/DOIs resolved |
| TriValve Registry | Tricuspid | published | [NCT03416166](https://clinicaltrials.gov/study/NCT03416166) | [PMID 31568868](https://pubmed.ncbi.nlm.nih.gov/31568868/) | IDs/DOIs resolved |
| EuroTR Registry | Tricuspid | published | [NCT06307262](https://clinicaltrials.gov/study/NCT06307262) | [PMID 38812292](https://pubmed.ncbi.nlm.nih.gov/38812292/) | IDs/DOIs resolved |
| TVT Registry — TTVR | Tricuspid | published | — | [PMID 41973411](https://pubmed.ncbi.nlm.nih.gov/41973411/) | IDs/DOIs resolved |
| PASTE | Tricuspid | published | [NCT05328284](https://clinicaltrials.gov/study/NCT05328284) | [PMID 39466215](https://pubmed.ncbi.nlm.nih.gov/39466215/) | IDs/DOIs resolved |
