# Pre-existing work disclosure

LabRecall AI is new work started during the contest submission period.

The entrant previously built ReproFrame AI, a separate scientific-visual provenance
application for another hackathon. That work suggested the broad research-operations
problem domain, but no ReproFrame source files, assets, deployment configuration, cloud
resources, stored data, or credentials were copied into LabRecall.

LabRecall has a different product action and architecture: it retrieves historical
pipeline failures, proposes bounded repairs, records human outcomes, and turns successful
outcomes into governed long-term memory using CockroachDB and AWS. ReproFrame generates
and verifies visual media using Genblaze and Backblaze B2.

Standard open-source Python libraries are used under their published licenses. Official
CockroachDB Agent Skills are pinned unchanged as a Git submodule, used for database
review, and attributed in `OPEN_SOURCE_REUSE.md` and `SKILL_EVIDENCE.md`.
