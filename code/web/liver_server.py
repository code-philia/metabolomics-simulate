import eventlet
eventlet.monkey_patch()

import sys
import os
import json
import yaml  # 需要安装: pip install pyyaml
from pathlib import Path
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from simulate import LiverMetabolismSystem, MetabolicEnvironment
except ImportError:
    print("错误：无法找到 simulate.py")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class WebMetabolicEnvironment(MetabolicEnvironment):
    def __init__(self):
        super().__init__()
        self.last_step_rates = {}
        self.last_step_metabolites = {}

    def update_history(self, t):
        self.last_step_rates = {k: float(v) for k, v in self.current_rates.items()}
        self.last_step_metabolites = {k: float(v) for k, v in self.metabolites.items()}
        super().update_history(t)

class WebLiveLiverSystem(LiverMetabolismSystem):
    def step_with_broadcast(self, hour_float, total_minutes):
        self.step(hour_float)
        socketio.emit('rate_update', {
            'minute': total_minutes,
            'rates': self.env.last_step_rates,
            'metabolites': self.env.last_step_metabolites
        })
        socketio.sleep(0.02)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_config')
def get_config():
    base_path = os.path.dirname(os.path.abspath(__file__))
    # 加载 层次结构 配置
    json_path = os.path.join(base_path, 'simulate_interface.json')
    # 加载 代谢物约束 配置
    yaml_path = os.path.join(base_path, 'metabolite_constraints.yaml')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            interface_data = json.load(f)
        
        constraints = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                # 转换为以变量名为 key 的字典方便前端查询
                for item in yaml_data.get('metabolites', []):
                    for var_name in item.get('variable_names', []):
                        constraints[var_name] = {
                            "min": item['normal_range']['min'],
                            "max": item['normal_range']['max'],
                            "name": item['name']
                        }
        
        return jsonify({
            "hierarchy": interface_data['hierarchy'],
            "reactions": interface_data['reactions'],
            "constraints": constraints
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('start_simulation')
def handle_start(data):
    env = WebMetabolicEnvironment()
    system = WebLiveLiverSystem(env)
    total_duration = int(data.get('duration', 120))
    events = data.get('events', [])
    
    for tt in range(total_duration + 1):
        for event in events:
            if int(event['time']) == tt:
                sub = event['substance']
                amt = float(event['amount'])
                if sub in env.metabolites:
                    env.metabolites[sub] += amt
        system.step_with_broadcast(tt/60.0, tt)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)