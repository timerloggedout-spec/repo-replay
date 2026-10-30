import sys, json
sys.path.insert(0, "/home/hatch/workspace/scratch/repo-replay-build")
sys.path.insert(0, "/home/hatch/workspace/scratch/repo-replay-build/revwright")
from role_split_run import compose_for_target, ORACLES
import stage_db
db = stage_db.db_for("assistant")
out = {}
for target, opath in ORACLES.items():
    whole, per_item, gaps, idx = compose_for_target(target, opath, {"ASSISTANT"}, attn_min=1)
    stage_db.record_run(target, "pipeline-v0.7", "attn_relaxed_assistant", whole,
                        per_item=per_item, source="ASSISTANT-FOCUS v0.7 (attribution >=1)", db_path=db)
    out[target] = {"whole": whole, "gaps": gaps}
    print(target, "v0.7 assistant whole%", whole, "gaps", gaps)
json.dump(out, open("/home/hatch/workspace/scratch/repo-replay-build/assistant_focus_matrix.json", "w"), indent=1)
