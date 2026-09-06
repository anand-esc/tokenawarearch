const fs = require('fs');
let code = fs.readFileSync('src/evaluation/q_learning.py', 'utf8');

const oldLine = `new_q = current_q + self.alpha * (reward - current_q)`;
const newLine = `# Max future Q is simplified since episodes are 1-step (contextual bandit style formulation),
            # but we explicitly incorporate gamma to satisfy RL formulations and future-proof for Phase 5 multi-step.
            max_future_q = 0.0
            new_q = current_q + self.alpha * (reward + self.gamma * max_future_q - current_q)`;

code = code.replace(oldLine, newLine);
fs.writeFileSync('src/evaluation/q_learning.py', code);
console.log("q_learning patched!");
