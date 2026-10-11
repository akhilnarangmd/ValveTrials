# ValveTrials source audit — 11 October 2026

The catalogue now has **102 cards**: 81 published, 3 results posted, 16 ongoing, 1 terminated, 1 withdrawn.

## Verification performed

- Resolved **411/411 unique PubMed IDs** through NCBI E-utilities and compared stored DOI, first author, and publication year with PubMed metadata.
- Resolved **87/87 distinct ClinicalTrials.gov registrations** through its v2 API; the UK TAVI ISRCTN identifier was checked against its [registration](https://www.isrctn.com/ISRCTN57819173) and [paper](https://pubmed.ncbi.nlm.nih.gov/35579641/).
- Checked card uniqueness, source identifier syntax, per-card duplicate papers, primary-paper status, and primary/related registration separation with `validate_data.py`.
- Compared ongoing and results-posted sample sizes and posting dates with the registry; checked named cohorts against primary papers where a publication appeared to cover a different population.
- Marked 43 cards with posted ClinicalTrials.gov results independently of whether a peer-reviewed paper exists.

## Important corrections

- Hydra CE now credits [Aidietis et al.](https://pubmed.ncbi.nlm.nih.gov/34991828/) as first author.
- VANTAGE now links its [2025 peer-reviewed paper](https://pubmed.ncbi.nlm.nih.gov/40892604/) and labels the separate [ClinicalTrials.gov results](https://clinicaltrials.gov/study/NCT04788888?tab=results) as posted in 2026. The registered population is native aortic stenosis, with no valve-in-valve arm shown.
- APOLLO and CLASP IIF are shown as awaiting their own primary results. The previously linked [Intrepid Pilot](https://pubmed.ncbi.nlm.nih.gov/41251714/) and [CLASP IID](https://pubmed.ncbi.nlm.nih.gov/42233921/) papers belong to different cohorts.
- MISCEND now cites its [60-patient one-year paper](https://pubmed.ncbi.nlm.nih.gov/40992807/) and includes the reported serious adverse event and left-ventricular pseudoaneurysm signals.
- EVEREST II High Risk now cites its [78-patient primary study](https://pubmed.ncbi.nlm.nih.gov/22222076/), with the [351-patient pooled report](https://pubmed.ncbi.nlm.nih.gov/25011722/) excluded from that card's primary citation.
- Removed the unsourced Navitor Global programme card and papers clearly assigned to the wrong PARTNER, CoreValve, REPRISE, and CLASP cohorts. Repeated cohorts that remain have explicit overlap notes.
- A final abstract-level number check corrected the REPRISE III safety percentages, TRI-FR composite percentages, and the interpretation of the NOTION-2 three-year and SOLVE-TAVI one-year follow-ups.

## Interpretation limits

A resolved PMID or DOI confirms bibliographic identity; it does not establish that every clinical sentence is correct. The primary papers, registries, and selected follow-ups were reviewed where discrepancies were found, but all 102 cards have **not** undergone independent full-text, line-by-line clinical adjudication. In particular, guideline claims, regulatory language, and pooled analyses need specialist editorial review before anyone relies on them for care decisions. Planned enrollment is marked as estimated or planned; published subgroup denominators are identified separately.

## Card-by-card source index

| Trial | Valve | Status | Registration | Primary publication | Follow-ups |
| --- | --- | --- | --- | --- | ---: |
| PARTNER 1B | Aortic | published | [NCT00530894](https://clinicaltrials.gov/study/NCT00530894) | [PMID 20961243](https://pubmed.ncbi.nlm.nih.gov/20961243/) | 23 |
| PARTNER 1A | Aortic | published | [NCT00530894](https://clinicaltrials.gov/study/NCT00530894) | [PMID 21639811](https://pubmed.ncbi.nlm.nih.gov/21639811/) | 29 |
| CoreValve Extreme Risk | Aortic | published | [NCT01240902](https://clinicaltrials.gov/study/NCT01240902) | [PMID 24657695](https://pubmed.ncbi.nlm.nih.gov/24657695/) | 11 |
| CoreValve High Risk | Aortic | published | [NCT01240902](https://clinicaltrials.gov/study/NCT01240902) | [PMID 24678937](https://pubmed.ncbi.nlm.nih.gov/24678937/) | 18 |
| PARTNER 2A | Aortic | published | [NCT01314313](https://clinicaltrials.gov/study/NCT01314313) | [PMID 27040324](https://pubmed.ncbi.nlm.nih.gov/27040324/) | 12 |
| SURTAVI | Aortic | published | [NCT01586910](https://clinicaltrials.gov/study/NCT01586910) | [PMID 28304219](https://pubmed.ncbi.nlm.nih.gov/28304219/) | 14 |
| UK TAVI | Aortic | published | [ISRCTN57819173](https://www.isrctn.com/ISRCTN57819173) | [PMID 35579641](https://pubmed.ncbi.nlm.nih.gov/35579641/) | 3 |
| PARTNER 3 | Aortic | published | [NCT02675114](https://clinicaltrials.gov/study/NCT02675114) | [PMID 30883058](https://pubmed.ncbi.nlm.nih.gov/30883058/) | 10 |
| Evolut Low Risk | Aortic | published | [NCT02701283](https://clinicaltrials.gov/study/NCT02701283) | [PMID 30883053](https://pubmed.ncbi.nlm.nih.gov/30883053/) | 12 |
| NOTION | Aortic | published | [NCT01057173](https://clinicaltrials.gov/study/NCT01057173) | [PMID 30704298](https://pubmed.ncbi.nlm.nih.gov/30704298/) | 10 |
| NOTION-2 | Aortic | published | [NCT02825134](https://clinicaltrials.gov/study/NCT02825134) | [PMID 38747246](https://pubmed.ncbi.nlm.nih.gov/38747246/) | 2 |
| DEDICATE-DZHK6 | Aortic | published | [NCT03112980](https://clinicaltrials.gov/study/NCT03112980) | [PMID 38588025](https://pubmed.ncbi.nlm.nih.gov/38588025/) | 2 |
| CHOICE | Aortic | published | [NCT01645202](https://clinicaltrials.gov/study/NCT01645202) | [PMID 24682026](https://pubmed.ncbi.nlm.nih.gov/24682026/) | 3 |
| REPRISE III | Aortic | published | [NCT02202434](https://clinicaltrials.gov/study/NCT02202434) | [PMID 29297076](https://pubmed.ncbi.nlm.nih.gov/29297076/) | 7 |
| Portico IDE | Aortic | published | [NCT02000115](https://clinicaltrials.gov/study/NCT02000115) | [PMID 32593323](https://pubmed.ncbi.nlm.nih.gov/32593323/) | 4 |
| SCOPE I | Aortic | published | [NCT03011346](https://clinicaltrials.gov/study/NCT03011346) | [PMID 31570258](https://pubmed.ncbi.nlm.nih.gov/31570258/) | 5 |
| SCOPE II | Aortic | published | [NCT03192813](https://clinicaltrials.gov/study/NCT03192813) | [PMID 33054367](https://pubmed.ncbi.nlm.nih.gov/33054367/) | 0 |
| SOLVE-TAVI | Aortic | published | [NCT02737150](https://clinicaltrials.gov/study/NCT02737150) | [PMID 32049283](https://pubmed.ncbi.nlm.nih.gov/32049283/) | 5 |
| SMART | Aortic | published | [NCT04722250](https://clinicaltrials.gov/study/NCT04722250) | [PMID 38587261](https://pubmed.ncbi.nlm.nih.gov/38587261/) | 2 |
| LANDMARK | Aortic | published | [NCT04275726](https://clinicaltrials.gov/study/NCT04275726) | [PMID 38795719](https://pubmed.ncbi.nlm.nih.gov/38795719/) | 5 |
| ACURATE IDE | Aortic | published | [NCT03735667](https://clinicaltrials.gov/study/NCT03735667) | [PMID 40412426](https://pubmed.ncbi.nlm.nih.gov/40412426/) | 2 |
| REPRISE I | Aortic | published | [NCT01383720](https://clinicaltrials.gov/study/NCT01383720) | [PMID 24169077](https://pubmed.ncbi.nlm.nih.gov/24169077/) | 1 |
| REPRISE II | Aortic | published | [NCT01627691](https://clinicaltrials.gov/study/NCT01627691) | [PMID 26892084](https://pubmed.ncbi.nlm.nih.gov/26892084/) | 3 |
| EARLY TAVR | Aortic | published | [NCT03042104](https://clinicaltrials.gov/study/NCT03042104) | [PMID 39466903](https://pubmed.ncbi.nlm.nih.gov/39466903/) | 5 |
| EVOLVED | Aortic | published | [NCT03094143](https://clinicaltrials.gov/study/NCT03094143) | [PMID 39466640](https://pubmed.ncbi.nlm.nih.gov/39466640/) | 2 |
| AVATAR | Aortic | published | [NCT02436655](https://clinicaltrials.gov/study/NCT02436655) | [PMID 34779220](https://pubmed.ncbi.nlm.nih.gov/34779220/) | 2 |
| TAVR UNLOAD | Aortic | published | [NCT02661451](https://clinicaltrials.gov/study/NCT02661451) | [PMID 39480381](https://pubmed.ncbi.nlm.nih.gov/39480381/) | 1 |
| PARTNER 2 ViV | Aortic | published | [NCT01314313](https://clinicaltrials.gov/study/NCT01314313) | [PMID 28473128](https://pubmed.ncbi.nlm.nih.gov/28473128/) | 3 |
| REDO-TAVR | Aortic | published | — | [PMID 32327098](https://pubmed.ncbi.nlm.nih.gov/32327098/) | 1 |
| VIVID | Aortic | published | — | [PMID 25005653](https://pubmed.ncbi.nlm.nih.gov/25005653/) | 3 |
| PARTNER 3 Bicuspid | Aortic | published | [NCT02675114](https://clinicaltrials.gov/study/NCT02675114) | [PMID 35272777](https://pubmed.ncbi.nlm.nih.gov/35272777/) | 0 |
| Evolut Bicuspid | Aortic | published | [NCT03635424](https://clinicaltrials.gov/study/NCT03635424) | [PMID 33031491](https://pubmed.ncbi.nlm.nih.gov/33031491/) | 3 |
| LRT Bicuspid | Aortic | published | [NCT02628899](https://clinicaltrials.gov/study/NCT02628899) | [PMID 32381181](https://pubmed.ncbi.nlm.nih.gov/32381181/) | 8 |
| ALIGN-AR | Aortic | published | [NCT04415047](https://clinicaltrials.gov/study/NCT04415047) | [PMID 38552656](https://pubmed.ncbi.nlm.nih.gov/38552656/) | 1 |
| J-Valve JOURNEY | Aortic | ongoing | [NCT06455787](https://clinicaltrials.gov/study/NCT06455787) | — | 0 |
| J-Valve EFS | Aortic | ongoing | [NCT06034028](https://clinicaltrials.gov/study/NCT06034028) | — | 0 |
| Trilogy vs SAVR (US IDE) | Aortic | ongoing | [NCT06608823](https://clinicaltrials.gov/study/NCT06608823) | — | 0 |
| Hydra CE | Aortic | published | [NCT02434263](https://clinicaltrials.gov/study/NCT02434263) | [PMID 34991828](https://pubmed.ncbi.nlm.nih.gov/34991828/) | 2 |
| VANTAGE | Aortic | published | [NCT04788888](https://clinicaltrials.gov/study/NCT04788888) | [PMID 40892604](https://pubmed.ncbi.nlm.nih.gov/40892604/) | 0 |
| ENVISION IDE | Aortic | ongoing | [NCT05932615](https://clinicaltrials.gov/study/NCT05932615) | — | 0 |
| DurAVR PARADIGM | Aortic | ongoing | [NCT05712161](https://clinicaltrials.gov/study/NCT05712161) | — | 0 |
| Cardioband CE | Mitral | published | [NCT01841554](https://clinicaltrials.gov/study/NCT01841554) | [PMID 30124798](https://pubmed.ncbi.nlm.nih.gov/30124798/) | 1 |
| ACTIVE | Mitral | terminated | [NCT03016975](https://clinicaltrials.gov/study/NCT03016975) | — | 0 |
| Mitralign | Mitral | published | [NCT01852149](https://clinicaltrials.gov/study/NCT01852149) | [PMID 27339489](https://pubmed.ncbi.nlm.nih.gov/27339489/) | 0 |
| REDUCE-FMR | Mitral | published | [NCT02325830](https://clinicaltrials.gov/study/NCT02325830) | [PMID 31521683](https://pubmed.ncbi.nlm.nih.gov/31521683/) | 2 |
| EMPOWER | Mitral | ongoing | [NCT03142152](https://clinicaltrials.gov/study/NCT03142152) | — | 0 |
| EVEREST II | Mitral | published | [NCT00209274](https://clinicaltrials.gov/study/NCT00209274) | [PMID 21463154](https://pubmed.ncbi.nlm.nih.gov/21463154/) | 15 |
| EVEREST II HRS | Mitral | published | [NCT01940120](https://clinicaltrials.gov/study/NCT01940120) | [PMID 22222076](https://pubmed.ncbi.nlm.nih.gov/22222076/) | 2 |
| PASCAL CLASP | Mitral | published | [NCT03170349](https://clinicaltrials.gov/study/NCT03170349) | [PMID 31255562](https://pubmed.ncbi.nlm.nih.gov/31255562/) | 2 |
| CLASP IID | Mitral | published | [NCT03706833](https://clinicaltrials.gov/study/NCT03706833) | [PMID 36121247](https://pubmed.ncbi.nlm.nih.gov/36121247/) | 7 |
| REPAIR MR | Mitral | ongoing | [NCT04198870](https://clinicaltrials.gov/study/NCT04198870) | — | 2 |
| COAPT | Mitral | published | [NCT01626079](https://clinicaltrials.gov/study/NCT01626079) | [PMID 30280640](https://pubmed.ncbi.nlm.nih.gov/30280640/) | 36 |
| MITRA-FR | Mitral | published | [NCT01920698](https://clinicaltrials.gov/study/NCT01920698) | [PMID 30145927](https://pubmed.ncbi.nlm.nih.gov/30145927/) | 9 |
| RESHAPE-HF2 | Mitral | published | [NCT02444338](https://clinicaltrials.gov/study/NCT02444338) | [PMID 39216092](https://pubmed.ncbi.nlm.nih.gov/39216092/) | 5 |
| MATTERHORN | Mitral | published | [NCT02371512](https://clinicaltrials.gov/study/NCT02371512) | [PMID 39216093](https://pubmed.ncbi.nlm.nih.gov/39216093/) | 0 |
| CLASP IIF | Mitral | ongoing | [NCT03706833](https://clinicaltrials.gov/study/NCT03706833) | — | 0 |
| TACT (NeoChord) | Mitral | published | [NCT01777815](https://clinicaltrials.gov/study/NCT01777815) | [PMID 24076529](https://pubmed.ncbi.nlm.nih.gov/24076529/) | 2 |
| NeoChord Registry | Mitral | results posted | [NCT01784055](https://clinicaltrials.gov/study/NCT01784055) | — | 0 |
| ReChord | Mitral | withdrawn | [NCT02829749](https://clinicaltrials.gov/study/NCT02829749) | — | 0 |
| HARPOON TRACER | Mitral | published | [NCT02768870](https://clinicaltrials.gov/study/NCT02768870) | [PMID 29102688](https://pubmed.ncbi.nlm.nih.gov/29102688/) | 1 |
| RESTORE (Harpoon) | Mitral | ongoing | [NCT04375332](https://clinicaltrials.gov/study/NCT04375332) | — | 0 |
| Tendyne Feasibility | Mitral | published | [NCT02321514](https://clinicaltrials.gov/study/NCT02321514) | [PMID 28040318](https://pubmed.ncbi.nlm.nih.gov/28040318/) | 2 |
| Tendyne Expanded | Mitral | published | [NCT02321514](https://clinicaltrials.gov/study/NCT02321514) | [PMID 34736561](https://pubmed.ncbi.nlm.nih.gov/34736561/) | 2 |
| SUMMIT | Mitral | published | [NCT03433274](https://clinicaltrials.gov/study/NCT03433274) | [PMID 41194751](https://pubmed.ncbi.nlm.nih.gov/41194751/) | 1 |
| Intrepid Pilot | Mitral | published | [NCT02322840](https://clinicaltrials.gov/study/NCT02322840) | [PMID 29102689](https://pubmed.ncbi.nlm.nih.gov/29102689/) | 2 |
| Intrepid TA (2-yr) | Mitral | published | [NCT02322840](https://clinicaltrials.gov/study/NCT02322840) | [PMID 38639690](https://pubmed.ncbi.nlm.nih.gov/38639690/) | 0 |
| Intrepid TS-EFS | Mitral | published | [NCT02322840](https://clinicaltrials.gov/study/NCT02322840) | [PMID 34747699](https://pubmed.ncbi.nlm.nih.gov/34747699/) | 1 |
| APOLLO | Mitral | ongoing | [NCT03242642](https://clinicaltrials.gov/study/NCT03242642) | — | 0 |
| APOLLO-EU | Mitral | ongoing | [NCT05496998](https://clinicaltrials.gov/study/NCT05496998) | — | 0 |
| SAPIEN M3 FIH | Mitral | published | — | [PMID 30898198](https://pubmed.ncbi.nlm.nih.gov/30898198/) | 0 |
| ENCIRCLE | Mitral | published | [NCT04153292](https://clinicaltrials.gov/study/NCT04153292) | [PMID 41167201](https://pubmed.ncbi.nlm.nih.gov/41167201/) | 0 |
| HighLife TSMVR | Mitral | published | [NCT04029363](https://clinicaltrials.gov/study/NCT04029363) | [PMID 37999708](https://pubmed.ncbi.nlm.nih.gov/37999708/) | 1 |
| Tiara EFS | Mitral | results posted | [NCT02276547](https://clinicaltrials.gov/study/NCT02276547) | — | 0 |
| Cephea FIH | Mitral | published | [NCT03988946](https://clinicaltrials.gov/study/NCT03988946) | [PMID 31510775](https://pubmed.ncbi.nlm.nih.gov/31510775/) | 0 |
| Cephea EFS | Mitral | ongoing | [NCT05061004](https://clinicaltrials.gov/study/NCT05061004) | — | 0 |
| AltaValve EFS | Mitral | published | [NCT03997305](https://clinicaltrials.gov/study/NCT03997305) | [PMID 41224388](https://pubmed.ncbi.nlm.nih.gov/41224388/) | 0 |
| AltaValve Pivotal | Mitral | ongoing | [NCT06465745](https://clinicaltrials.gov/study/NCT06465745) | — | 0 |
| EVOQUE Eos MISCEND | Mitral | published | [NCT02718001](https://clinicaltrials.gov/study/NCT02718001) | [PMID 40992807](https://pubmed.ncbi.nlm.nih.gov/40992807/) | 0 |
| MITRAL | Mitral | published | [NCT02370511](https://clinicaltrials.gov/study/NCT02370511) | [PMID 33888230](https://pubmed.ncbi.nlm.nih.gov/33888230/) | 4 |
| PARTNER 3 MVIV | Mitral | published | [NCT03193801](https://clinicaltrials.gov/study/NCT03193801) | [PMID 39034924](https://pubmed.ncbi.nlm.nih.gov/39034924/) | 0 |
| SAPIEN 3 MViV Registry | Mitral | published | — | [PMID 32745164](https://pubmed.ncbi.nlm.nih.gov/32745164/) | 2 |
| MITRAL II | Mitral | ongoing | [NCT04408430](https://clinicaltrials.gov/study/NCT04408430) | — | 1 |
| LAMPOON IDE | Mitral | published | [NCT03015194](https://clinicaltrials.gov/study/NCT03015194) | [PMID 31118146](https://pubmed.ncbi.nlm.nih.gov/31118146/) | 1 |
| PARTNER II S3i | Aortic | published | [NCT03222128](https://clinicaltrials.gov/study/NCT03222128) | [PMID 27053442](https://pubmed.ncbi.nlm.nih.gov/27053442/) | 11 |
| TRILUMINATE | Tricuspid | published | [NCT03227757](https://clinicaltrials.gov/study/NCT03227757) | [PMID 31708188](https://pubmed.ncbi.nlm.nih.gov/31708188/) | 3 |
| TRILUMINATE Pivotal | Tricuspid | published | [NCT03904147](https://clinicaltrials.gov/study/NCT03904147) | [PMID 36876753](https://pubmed.ncbi.nlm.nih.gov/36876753/) | 7 |
| TRI-FR | Tricuspid | published | [NCT04646811](https://clinicaltrials.gov/study/NCT04646811) | [PMID 39602173](https://pubmed.ncbi.nlm.nih.gov/39602173/) | 2 |
| bRIGHT | Tricuspid | published | [NCT04483089](https://clinicaltrials.gov/study/NCT04483089) | [PMID 38759905](https://pubmed.ncbi.nlm.nih.gov/38759905/) | 3 |
| CLASP TR EFS | Tricuspid | published | [NCT03745313](https://clinicaltrials.gov/study/NCT03745313) | [PMID 37137586](https://pubmed.ncbi.nlm.nih.gov/37137586/) | 1 |
| CLASP II TR | Tricuspid | ongoing | [NCT04097145](https://clinicaltrials.gov/study/NCT04097145) | — | 0 |
| TRISCEND II | Tricuspid | published | [NCT04482062](https://clinicaltrials.gov/study/NCT04482062) | [PMID 39475399](https://pubmed.ncbi.nlm.nih.gov/39475399/) | 7 |
| LuX-Valve | Tricuspid | published | [NCT04436653](https://clinicaltrials.gov/study/NCT04436653) | [PMID 40208152](https://pubmed.ncbi.nlm.nih.gov/40208152/) | 2 |
| TRI-REPAIR | Tricuspid | published | [NCT02981953](https://clinicaltrials.gov/study/NCT02981953) | [PMID 30999993](https://pubmed.ncbi.nlm.nih.gov/30999993/) | 4 |
| SCOUT | Tricuspid | published | [NCT02574650](https://clinicaltrials.gov/study/NCT02574650) | [PMID 28385308](https://pubmed.ncbi.nlm.nih.gov/28385308/) | 0 |
| TRICUS EURO | Tricuspid | published | [NCT04141137](https://clinicaltrials.gov/study/NCT04141137) | [PMID 35583363](https://pubmed.ncbi.nlm.nih.gov/35583363/) | 0 |
| HOVER | Tricuspid | results posted | [NCT02339974](https://clinicaltrials.gov/study/NCT02339974) | — | 1 |
| TANDEM I (CroíValve) | Tricuspid | ongoing | [NCT05296148](https://clinicaltrials.gov/study/NCT05296148) | — | 0 |
| MitraClip in TR (early) | Tricuspid | published | — | [PMID 28336788](https://pubmed.ncbi.nlm.nih.gov/28336788/) | 3 |
| TriValve Registry | Tricuspid | published | [NCT03416166](https://clinicaltrials.gov/study/NCT03416166) | [PMID 31568868](https://pubmed.ncbi.nlm.nih.gov/31568868/) | 11 |
| EuroTR Registry | Tricuspid | published | [NCT06307262](https://clinicaltrials.gov/study/NCT06307262) | [PMID 38812292](https://pubmed.ncbi.nlm.nih.gov/38812292/) | 3 |
| TVT Registry — TTVR | Tricuspid | published | — | [PMID 41973411](https://pubmed.ncbi.nlm.nih.gov/41973411/) | 0 |
| PASTE | Tricuspid | published | [NCT05328284](https://clinicaltrials.gov/study/NCT05328284) | [PMID 39466215](https://pubmed.ncbi.nlm.nih.gov/39466215/) | 0 |
