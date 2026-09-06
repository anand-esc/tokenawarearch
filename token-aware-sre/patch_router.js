const fs = require('fs');
let code = fs.readFileSync('src/router/dynamic_router.py', 'utf8');

// Add import
if (!code.includes('from src.evaluation.q_learning import QLearningRouter')) {
    code = code.replace(
        "from .budgeting import TokenBudgeter",
        "from .budgeting import TokenBudgeter\nfrom src.evaluation.q_learning import QLearningRouter"
    );
}

// Add Initialization
if (!code.includes('self.q_router = QLearningRouter()')) {
    code = code.replace(
        "self.budgeter = TokenBudgeter()",
        "self.budgeter = TokenBudgeter()\n            self.q_router = QLearningRouter()"
    );
}

// Update Routing Logic
const oldRoutingLogic = `            # 3. Routing Logic: Match Complexity vs Budget
            if budget.get("requires_local_only", False):
                model_target = "LOCAL_SLM"
                reason = "Budget restricted to $0.00 due to low severity."
            elif complexity >= 7 and budget.get("max_spend_usd", 0) > 0.0:
                model_target = "CLOUD_LLM"
                reason = "High complexity requires frontier model. Budget is available."
            else:
                model_target = "LOCAL_SLM"
                reason = "Low to moderate complexity. Local SLM is sufficient and saves budget."`;

const newRoutingLogic = `            # 3. Routing Logic: Match Complexity vs Budget via Q-Learning!
            if budget.get("requires_local_only", False):
                model_target = "LOCAL_SLM"
                reason = "Budget restricted to $0.00 due to low severity."
            else:
                # Query the RL Brain!
                action = self.q_router.choose_action(severity, complexity)
                if action == 1 and budget.get("max_spend_usd", 0) > 0.0:
                    model_target = "CLOUD_LLM"
                    reason = "Q-Learning Brain chose Cloud LLM. Budget is available."
                else:
                    model_target = "LOCAL_SLM"
                    reason = "Q-Learning Brain chose Local SLM (or insufficient budget for Cloud override)."`;

code = code.replace(oldRoutingLogic, newRoutingLogic);
fs.writeFileSync('src/router/dynamic_router.py', code);
console.log("dynamic_router patched!");
