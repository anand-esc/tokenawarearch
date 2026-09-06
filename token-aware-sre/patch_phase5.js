const fs = require('fs');
let code = fs.readFileSync('src/api.py', 'utf8');

if (!code.includes('Phase 5 integration')) {
    code = code.replace(
        "from src.evaluation.evaluator import ActionEvaluator",
        "from src.evaluation.evaluator import ActionEvaluator\nfrom src.evaluation.phase5_finetuning import FineTuningPipeline"
    );
    
    code = code.replace(
        "evaluator = ActionEvaluator()",
        "evaluator = ActionEvaluator()\nfine_tuner = FineTuningPipeline()"
    );
    
    const oldReward = `    q_router.update(req.severity, req.complexity, action_idx, calculated_reward)
    return {"status": "success", "message": f"Q-Table updated with {calculated_reward}"}`;
    
    const newReward = `    q_router.update(req.severity, req.complexity, action_idx, calculated_reward)
    
    # Phase 5 integration: Store highly successful resolutions for QLoRA Fine-Tuning
    if calculated_reward >= 10.0 and req.model_target == "LOCAL_SLM":
        # In a real scenario we'd fetch the actual script payload, but we log the trigger
        fine_tuner.log_successful_resolution(f"Sev {req.severity} Comp {req.complexity} Incident", "Executed Script Placeholder", calculated_reward)
        
    return {"status": "success", "message": f"Q-Table updated with {calculated_reward}. Phase 5 buffer checked."}`;
    
    code = code.replace(oldReward, newReward);
    fs.writeFileSync('src/api.py', code);
    console.log("Phase 5 wired into api.py!");
}
