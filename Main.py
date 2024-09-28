import base64
import zlib
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox

def parse_blueprint(blueprint_string):
    # Remove version number (the '0' at the start)
    if blueprint_string.startswith('0'):
        blueprint_string = blueprint_string[1:]
    
    # Decode from base64
    compressed_data = base64.b64decode(blueprint_string)
    
    # Decompress using zlib
    decompressed_data = zlib.decompress(compressed_data)
    
    # Load JSON data
    blueprint_json = json.loads(decompressed_data)
    
    return blueprint_json

def analyze_space_efficiency(blueprint_data):
    entities = blueprint_data['blueprint'].get('entities', [])
    
    # Create a grid or spatial index for quick neighbor lookups
    entity_positions = {}
    for entity in entities:
        pos = (entity['position']['x'], entity['position']['y'])
        entity_positions[pos] = entity['name']
    
    suggestions = []
    for entity in entities:
        x = entity['position']['x']
        y = entity['position']['y']
        neighbors = [
            (x + dx, y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if not (dx == 0 and dy == 0)
        ]
        empty_neighbors = [pos for pos in neighbors if pos not in entity_positions]
        
        if empty_neighbors:
            suggestions.append(f"Entity '{entity['name']}' at ({x}, {y}) has empty adjacent spaces.")
        
        # Check for compact design
        if entity['name'] in ['assembling-machine-1', 'assembling-machine-2', 'assembling-machine-3']:
            if len(empty_neighbors) > 2:
                suggestions.append(f"Assembling machine '{entity['name']}' at ({x}, {y}) could be placed more compactly.")
        
        # Check for efficient use of underground belts and pipes
        if entity['name'] in ['underground-belt', 'pipe-to-ground']:
            underground_partner = None
            for dx in range(-5, 6):  # Check up to 5 tiles in each direction
                for dy in range(-5, 6):
                    check_pos = (x + dx, y + dy)
                    if check_pos in entity_positions and entity_positions[check_pos] == entity['name']:
                        underground_partner = check_pos
                        break
                if underground_partner:
                    break
            
            if not underground_partner:
                suggestions.append(f"Underground entity '{entity['name']}' at ({x}, {y}) doesn't seem to have a partner within range.")
            else:
                distance = max(abs(underground_partner[0] - x), abs(underground_partner[1] - y))
                if distance < 4:  # Assuming max underground distance is 4
                    suggestions.append(f"Underground connection from ({x}, {y}) to {underground_partner} could potentially span a greater distance.")
    
    # Check for overall layout compactness
    total_entities = len(entities)
    total_area = (max(e['position']['x'] for e in entities) - min(e['position']['x'] for e in entities)) * \
                 (max(e['position']['y'] for e in entities) - min(e['position']['y'] for e in entities))
    density = total_entities / total_area
    
    if density < 0.5:  # This threshold can be adjusted
        suggestions.append("The overall layout seems sparse. Consider a more compact design to improve space efficiency.")
    
    return suggestions


def analyze_throughput(blueprint_data):
    suggestions = []
    entities = blueprint_data['blueprint'].get('entities', [])
    
    belt_counts = {'transport-belt': 0, 'fast-transport-belt': 0, 'express-transport-belt': 0}
    inserter_counts = {'inserter': 0, 'fast-inserter': 0, 'stack-inserter': 0}
    
    for entity in entities:
        # Analyze belt types
        if entity['name'] in belt_counts:
            belt_counts[entity['name']] += 1
        
        # Analyze inserter types
        if entity['name'] in inserter_counts:
            inserter_counts[entity['name']] += 1
        
        # Check for balanced inputs using splitters
        if entity['name'] == 'splitter':
            nearby_entities = [e for e in entities if abs(e['position']['x'] - entity['position']['x']) <= 2 and abs(e['position']['y'] - entity['position']['y']) <= 2]
            if len([e for e in nearby_entities if 'transport-belt' in e['name']]) < 3:
                suggestions.append(f"Splitter at ({entity['position']['x']}, {entity['position']['y']}) may not be fully utilized for balancing.")
    
    # Suggest belt upgrades
    if belt_counts['transport-belt'] > belt_counts['fast-transport-belt'] + belt_counts['express-transport-belt']:
        suggestions.append("Consider upgrading some yellow belts to red or blue belts to improve throughput in high-demand areas.")
    
    # Suggest inserter upgrades
    if inserter_counts['inserter'] > inserter_counts['fast-inserter'] + inserter_counts['stack-inserter']:
        suggestions.append("Upgrade some regular inserters to fast or stack inserters, especially in high-throughput areas.")
    
    # Check for potential bottlenecks
    high_throughput_areas = ['electronic-circuit', 'advanced-circuit', 'processing-unit', 'iron-plate', 'copper-plate', 'steel-plate']
    for entity in entities:
        if entity['name'] in high_throughput_areas:
            nearby_belts = [e for e in entities if 'transport-belt' in e['name'] and abs(e['position']['x'] - entity['position']['x']) <= 1 and abs(e['position']['y'] - entity['position']['y']) <= 1]
            if any('transport-belt' == belt['name'] for belt in nearby_belts):
                suggestions.append(f"Consider upgrading belts near {entity['name']} at ({entity['position']['x']}, {entity['position']['y']}) to higher tier for better throughput.")
    
    return suggestions


def analyze_power_efficiency(blueprint_data):
    suggestions = []
    entities = blueprint_data['blueprint'].get('entities', [])
    
    solar_panel_count = 0
    accumulator_count = 0
    module_slots = 0
    efficiency_modules = 0
    productivity_modules = 0
    speed_modules = 0
    
    high_power_consumers = ['electric-furnace', 'electric-mining-drill', 'assembling-machine-3', 'chemical-plant']
    
    for entity in entities:
        if entity['name'] == 'solar-panel':
            solar_panel_count += 1
        elif entity['name'] == 'accumulator':
            accumulator_count += 1
        
        # Check for module usage
        if 'items' in entity:
            for item in entity['items']:
                if 'module' in item:
                    module_slots += 1
                    if 'efficiency-module' in item:
                        efficiency_modules += 1
                    elif 'productivity-module' in item:
                        productivity_modules += 1
                    elif 'speed-module' in item:
                        speed_modules += 1
        
        # Suggest efficiency modules for high power consumers
        if entity['name'] in high_power_consumers and ('items' not in entity or not any('efficiency-module' in item for item in entity['items'])):
            suggestions.append(f"Consider adding Efficiency Modules to {entity['name']} at ({entity['position']['x']}, {entity['position']['y']}) to reduce power consumption.")
    
    # Analyze solar panel and accumulator ratio
    if solar_panel_count > 0 or accumulator_count > 0:
        ideal_ratio = 23 / 21  # Approximately 1.095
        actual_ratio = solar_panel_count / accumulator_count if accumulator_count > 0 else float('inf')
        if abs(actual_ratio - ideal_ratio) > 0.1:  # Allow for some deviation
            suggestions.append(f"The ratio of solar panels to accumulators is not optimal. Current ratio: {actual_ratio:.2f}, Ideal ratio: {ideal_ratio:.2f}")
    
    # Analyze module usage
    if module_slots > 0:
        if efficiency_modules / module_slots < 0.2:
            suggestions.append("Consider using more Efficiency Modules in machines to reduce power consumption.")
        if productivity_modules / module_slots < 0.3:
            suggestions.append("Increase the use of Productivity Modules in appropriate machines to improve resource efficiency.")
    
    return suggestions


def analyze_production_balancing(blueprint_data):
    suggestions = []
    entities = blueprint_data['blueprint'].get('entities', [])
    
    # Count different types of entities
    entity_counts = {}
    for entity in entities:
        entity_counts[entity['name']] = entity_counts.get(entity['name'], 0) + 1
    
    # Check smelting ratios
    iron_furnaces = entity_counts.get('stone-furnace', 0) + entity_counts.get('steel-furnace', 0) + entity_counts.get('electric-furnace', 0)
    steel_furnaces = entity_counts.get('steel-furnace', 0) + entity_counts.get('electric-furnace', 0)
    if iron_furnaces > 0 and steel_furnaces > 0:
        ideal_ratio = 5  # 5 iron furnaces to 1 steel furnace
        actual_ratio = iron_furnaces / steel_furnaces
        if abs(actual_ratio - ideal_ratio) > 0.5:
            suggestions.append(f"The ratio of iron to steel furnaces is not optimal. Current ratio: {actual_ratio:.2f}, Ideal ratio: {ideal_ratio}")
    
    # Check circuit production ratios
    copper_cable_assemblers = entity_counts.get('assembling-machine-1', 0) + entity_counts.get('assembling-machine-2', 0) + entity_counts.get('assembling-machine-3', 0)
    green_circuit_assemblers = copper_cable_assemblers // 3 * 2
    if copper_cable_assemblers > 0 and green_circuit_assemblers > 0:
        ideal_ratio = 3/2  # 3 copper cable assemblers to 2 green circuit assemblers
        actual_ratio = copper_cable_assemblers / green_circuit_assemblers
        if abs(actual_ratio - ideal_ratio) > 0.2:
            suggestions.append(f"The ratio of copper cable to green circuit assemblers is not optimal. Current ratio: {actual_ratio:.2f}, Ideal ratio: {ideal_ratio}")
    
    # Check mining to smelting ratio
    miners = entity_counts.get('electric-mining-drill', 0) + entity_counts.get('burner-mining-drill', 0)
    if miners > 0 and iron_furnaces > 0:
        ideal_ratio = 1  # Assuming 1 miner can support 1 furnace (this may vary based on game settings)
        actual_ratio = miners / iron_furnaces
        if abs(actual_ratio - ideal_ratio) > 0.2:
            suggestions.append(f"The ratio of miners to furnaces may not be balanced. Current ratio: {actual_ratio:.2f}, Consider adjusting for optimal production.")
    
    # Check for potential bottlenecks in production chains
    if entity_counts.get('assembling-machine-3', 0) > entity_counts.get('electronic-circuit', 0):
        suggestions.append("You may need more green circuit production to support your assembling machines.")
    
    if entity_counts.get('chemical-plant', 0) > entity_counts.get('oil-refinery', 0) * 3:
        suggestions.append("Consider adding more oil refineries to support your chemical plants.")
    
    return suggestions


def analyze_transport_optimization(blueprint_data):
    suggestions = []
    entities = blueprint_data['blueprint'].get('entities', [])
    
    belt_lengths = {'transport-belt': 0, 'fast-transport-belt': 0, 'express-transport-belt': 0}
    train_components = {'train-stop': 0, 'rail': 0, 'rail-signal': 0, 'rail-chain-signal': 0}
    
    for entity in entities:
        # Analyze belt usage
        if entity['name'] in belt_lengths:
            belt_lengths[entity['name']] += 1
        
        # Count train components
        if entity['name'] in train_components:
            train_components[entity['name']] += 1
    
    total_belt_length = sum(belt_lengths.values())
    
    # Suggest train system for long distances
    if total_belt_length > 1000:  # Arbitrary threshold, adjust as needed
        suggestions.append("Consider implementing a train system for long-distance transport to improve efficiency.")
    
    # Analyze existing train network
    if train_components['train-stop'] > 0:
        if train_components['rail-signal'] == 0 and train_components['rail-chain-signal'] == 0:
            suggestions.append("Your train network lacks signals. Add rail signals and chain signals to prevent deadlocks and improve efficiency.")
        
        signal_ratio = (train_components['rail-signal'] + train_components['rail-chain-signal']) / train_components['rail']
        if signal_ratio < 0.1:  # Arbitrary threshold, adjust as needed
            suggestions.append("Your train network may benefit from more signals to improve throughput.")
        
        if train_components['train-stop'] < 2:
            suggestions.append("Consider adding more train stops to distribute resources effectively across your factory.")
    
    # Suggest belt upgrades for high-throughput areas
    if belt_lengths['transport-belt'] > belt_lengths['fast-transport-belt'] + belt_lengths['express-transport-belt']:
        suggestions.append("Upgrade to faster belts in high-throughput areas to prevent bottlenecks.")
    
    # Check for potential long-distance belt transport
    max_x = max(entity['position']['x'] for entity in entities)
    min_x = min(entity['position']['x'] for entity in entities)
    max_y = max(entity['position']['y'] for entity in entities)
    min_y = min(entity['position']['y'] for entity in entities)
    
    blueprint_size = max(max_x - min_x, max_y - min_y)
    if blueprint_size > 200 and train_components['train-stop'] == 0:  # Arbitrary threshold, adjust as needed
        suggestions.append("Your blueprint covers a large area. Consider implementing a train network for more efficient long-distance transport.")
    
    return suggestions


def analyze_automation_and_circuits(blueprint_data):
    suggestions = []
    entities = blueprint_data['blueprint'].get('entities', [])
    
    circuit_network_components = {
        'arithmetic-combinator': 0,
        'decider-combinator': 0,
        'constant-combinator': 0,
        'programmable-speaker': 0,
        'power-switch': 0
    }
    
    logistics_components = {
        'logistic-chest-active-provider': 0,
        'logistic-chest-passive-provider': 0,
        'logistic-chest-storage': 0,
        'logistic-chest-buffer': 0,
        'logistic-chest-requester': 0,
        'roboport': 0
    }
    
    for entity in entities:
        # Count circuit network components
        if entity['name'] in circuit_network_components:
            circuit_network_components[entity['name']] += 1
        
        # Count logistics components
        if entity['name'] in logistics_components:
            logistics_components[entity['name']] += 1
        
        # Check for circuit conditions on inserters
        if 'inserter' in entity['name'] and 'control_behavior' in entity:
            if 'circuit_condition' in entity['control_behavior']:
                suggestions.append(f"Inserter at ({entity['position']['x']}, {entity['position']['y']}) is using circuit conditions. Good job on automation!")
    
    # Analyze circuit network usage
    total_circuit_components = sum(circuit_network_components.values())
    if total_circuit_components == 0:
        suggestions.append("Consider using circuit networks to optimize your factory. They can help control production and prevent overproduction.")
    elif total_circuit_components < 5:
        suggestions.append("You're using some circuit networks. Consider expanding their use for more complex automation.")
    else:
        suggestions.append("Great job utilizing circuit networks for automation!")
    
    # Analyze logistics system
    total_logistics_chests = sum(logistics_components.values()) - logistics_components['roboport']
    if logistics_components['roboport'] == 0:
        suggestions.append("Consider implementing a logistics system with roboports for more efficient item movement.")
    elif total_logistics_chests == 0:
        suggestions.append("You have roboports but no logistics chests. Add provider and requester chests to utilize your logistics network.")
    else:
        suggestions.append("Good use of a logistics network. Ensure provider chests are near production and requester chests near consumption for optimal efficiency.")
    
    # Check for balanced use of different chest types
    if logistics_components['logistic-chest-requester'] > 0 and logistics_components['logistic-chest-passive-provider'] == 0:
        suggestions.append("You're using requester chests but no passive provider chests. Consider adding passive providers for a more balanced logistics system.")
    
    return suggestions



def generate_optimization_report(analysis_results):
    report = "Factorio Blueprint Analysis Report\n"
    report += "================================\n\n"
    
    sections = [
        ("Space Efficiency", analysis_results['space_efficiency']),
        ("Throughput", analysis_results['throughput']),
        ("Power Efficiency", analysis_results['power_efficiency']),
        ("Production Balancing", analysis_results['production_balancing']),
        ("Transport Optimization", analysis_results['transport_optimization']),
        ("Automation and Circuits", analysis_results['automation_and_circuits'])
    ]
    
    for section_title, suggestions in sections:
        report += f"{section_title} Suggestions:\n"
        if suggestions:
            for suggestion in suggestions:
                report += f"- {suggestion}\n"
        else:
            report += "- No specific suggestions. Good job!\n"
        report += "\n"
    
    report += "Overall Assessment:\n"
    total_suggestions = sum(len(suggestions) for _, suggestions in sections)
    if total_suggestions == 0:
        report += "Excellent work! Your blueprint appears to be well-optimized in all areas.\n"
    elif total_suggestions < 5:
        report += "Great job! Your blueprint is well-designed with only a few minor optimization opportunities.\n"
    elif total_suggestions < 10:
        report += "Good work! Your blueprint has several areas for potential improvement, but it's on the right track.\n"
    else:
        report += "There are multiple opportunities to optimize your blueprint. Consider implementing the suggestions above to improve efficiency.\n"
    
    return report


def create_gui():
    def analyze_blueprint():
        blueprint_string = input_text.get("1.0", tk.END).strip()
        try:
            blueprint_data = parse_blueprint(blueprint_string)
            
            space_efficiency_results = analyze_space_efficiency(blueprint_data)
            throughput_results = analyze_throughput(blueprint_data)
            power_efficiency_results = analyze_power_efficiency(blueprint_data)
            production_balancing_results = analyze_production_balancing(blueprint_data)
            transport_optimization_results = analyze_transport_optimization(blueprint_data)
            automation_circuit_results = analyze_automation_and_circuits(blueprint_data)
            
            analysis_results = {
                'space_efficiency': space_efficiency_results,
                'throughput': throughput_results,
                'power_efficiency': power_efficiency_results,
                'production_balancing': production_balancing_results,
                'transport_optimization': transport_optimization_results,
                'automation_and_circuits': automation_circuit_results,
            }
            
            report = generate_optimization_report(analysis_results)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, report)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    root = tk.Tk()
    root.title("Factorio Blueprint Analyzer")
    root.geometry("800x600")

    input_label = tk.Label(root, text="Enter your Factorio blueprint string:")
    input_label.pack(pady=10)

    input_text = scrolledtext.ScrolledText(root, height=10)
    input_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    analyze_button = tk.Button(root, text="Analyze Blueprint", command=analyze_blueprint)
    analyze_button.pack(pady=10)

    output_label = tk.Label(root, text="Analysis Report:")
    output_label.pack(pady=10)

    output_text = scrolledtext.ScrolledText(root, height=15)
    output_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    root.mainloop()


def main():
    create_gui()

if __name__ == '__main__':
    main()
