import inquirer
import sys
import json
from Model import PCBuilder

class PCBuildCLI:
    def __init__(self):
        self.pc_builder = PCBuilder()
        self.selected_components = {}
    
    def get_component_choices(self, component_type):
        """Get all components of a specific type for selection"""
        components = self.pc_builder.get_components_by_type(component_type)
        choices = []
        for comp in components:
            # Create a readable display with specs
            specs_str = ", ".join([f"{k}: {v}" for k, v in comp.specs.items()])
            display_name = f"{comp.name} ({specs_str})"
            choices.append((display_name, comp))
        return choices
    
    def select_component(self, component_type):
        """Allow user to select a component of specific type"""
        print(f"\n📦 Select {component_type}:")
        print("-" * 40)
        
        choices = self.get_component_choices(component_type)
        if not choices:
            print(f"❌ No {component_type} components found in database!")
            return None
            
        # Add option to skip this component
        choices.append(("⏭️  Skip this component", None))
        
        questions = [
            inquirer.List(
                'component',
                message=f"Choose your {component_type}",
                choices=choices,
                carousel=True
            )
        ]
        
        answer = inquirer.prompt(questions)
        if answer and answer['component']:
            return answer['component']
        return None
    
    def display_selected_components(self):
        """Display currently selected components"""
        print("\n" + "="*50)
        print("🛠️  SELECTED COMPONENTS")
        print("="*50)
        
        if not self.selected_components:
            print("❌ No components selected yet!")
            return
            
        for comp_type, component in self.selected_components.items():
            specs_str = ", ".join([f"{k}: {v}" for k, v in component.specs.items()])
            print(f"✅ {comp_type}: {component.name}")
            print(f"   └─ Specs: {specs_str}")
        
        print("="*50)
    
    def validate_build(self):
        """Validate the selected components"""
        if not self.selected_components:
            print("\n❌ No components selected for validation!")
            return False, "No components selected"
            
        components_list = list(self.selected_components.values())
        is_valid, message = self.pc_builder.validate_compatibility(components_list)
        
        print("\n" + "="*50)
        print("🔍 COMPATIBILITY CHECK")
        print("="*50)
        
        if is_valid:
            print("✅ SUCCESS: Your build is compatible!")
            print(f"💬 {message}")
        else:
            print("❌ ERROR: Compatibility issue found!")
            print(f"💬 {message}")
            
        print("="*50)
        return is_valid, message
    
    def save_build_option(self):
        """Option to save the current build"""
        if not self.selected_components:
            print("\n❌ No components to save!")
            return
            
        # First validate the build
        is_valid, _ = self.validate_build()
        
        if not is_valid:
            questions = [
                inquirer.Confirm('save_anyway', 
                               message="Build has compatibility issues. Save anyway?",
                               default=False)
            ]
            answer = inquirer.prompt(questions)
            if not answer or not answer['save_anyway']:
                return
        
        # Get build name
        questions = [
            inquirer.Text('name', message="Enter a name for your build")
        ]
        
        answer = inquirer.prompt(questions)
        if answer and answer['name']:
            component_ids = [comp.id for comp in self.selected_components.values()]
            success, message = self.pc_builder.save_build(answer['name'], component_ids)
            
            if success:
                print(f"\n✅ {message}")
            else:
                print(f"\n❌ {message}")

    def insert_component(self):
        """Add a new component to the database"""
        print("\n" + "="*50)
        print("🔧 ADD NEW COMPONENT")
        print("="*50)
        
        # Get existing component types plus option for new type
        existing_types = self.pc_builder.get_distinct_component_types()
        type_choices = existing_types + ["➕ Add New Type"]
        
        questions = [
            inquirer.List('type',
                         message="Select component type",
                         choices=type_choices,
                         carousel=True)
        ]
        answer = inquirer.prompt(questions)
        if not answer:
            return
            
        if answer['type'] == "➕ Add New Type":
            questions = [
                inquirer.Text('new_type', message="Enter new component type")
            ]
            new_type_answer = inquirer.prompt(questions)
            if not new_type_answer or not new_type_answer['new_type']:
                return
            comp_type = new_type_answer['new_type']
        else:
            comp_type = answer['type']
        
        # Get component name
        questions = [
            inquirer.Text('name', message="Enter component name")
        ]
        answer = inquirer.prompt(questions)
        if not answer or not answer['name']:
            return
            
        comp_name = answer['name']
        
        # Get specs based on component type
        specs = {}
        if comp_type.upper() == "CPU":
            questions = [
                inquirer.Text('socket', message="Socket (e.g., LGA1700, AM4, AM5) - REQUIRED for compatibility"),
                inquirer.Text('tdp', message="TDP (e.g., 65W, 125W) - Optional")
            ]
            spec_answer = inquirer.prompt(questions)
            if spec_answer:
                specs = {k: v for k, v in spec_answer.items() if v}
                
        elif comp_type.upper() == "GPU":
            questions = [
                inquirer.Text('interface', message="Interface (e.g., PCIe 4.0) - REQUIRED for compatibility"),
                inquirer.Text('tdp', message="TDP (e.g., 220W) - Optional")
            ]
            spec_answer = inquirer.prompt(questions)
            if spec_answer:
                specs = {k: v for k, v in spec_answer.items() if v}
                
        elif comp_type.upper() == "RAM":
            questions = [
                inquirer.Text('type', message="RAM Type (e.g., DDR4, DDR5) - REQUIRED for compatibility"),
                inquirer.Text('speed', message="Speed (e.g., 3200MHz) - REQUIRED for compatibility")
            ]
            spec_answer = inquirer.prompt(questions)
            if spec_answer:
                specs = {k: v for k, v in spec_answer.items() if v}
                
        elif comp_type.upper() == "MOTHERBOARD":
            questions = [
                inquirer.Text('socket', message="Socket (e.g., LGA1700, AM4, AM5) - REQUIRED for compatibility"),
                inquirer.Text('ram_support', message="RAM Support (e.g., DDR4, DDR5, DDR4/DDR5) - REQUIRED"),
                inquirer.Text('max_ram_speed', message="Max RAM Speed (e.g., 3200MHz, 5600MHz) - REQUIRED"),
                inquirer.List('pcie_support', message="PCIe Support - REQUIRED", choices=["Yes", "No"], default="Yes"),
                inquirer.List('sata_support', message="SATA Support - REQUIRED", choices=["Yes", "No"], default="Yes"),
                inquirer.List('nvme_support', message="NVMe Support - REQUIRED", choices=["Yes", "No"], default="Yes")
            ]
            spec_answer = inquirer.prompt(questions)
            if spec_answer:
                specs = {k: v for k, v in spec_answer.items() if v}
                
        elif comp_type.upper() == "STORAGE":
            questions = [
                inquirer.Text('interface', message="Interface (e.g., NVMe, SATA) - REQUIRED for compatibility")
            ]
            spec_answer = inquirer.prompt(questions)
            if spec_answer:
                specs = {k: v for k, v in spec_answer.items() if v}
        else:
            # For other component types, ask for custom specs
            print(f"\nFor {comp_type}, please enter specifications needed for compatibility:")
            questions = [
                inquirer.Text('spec1', message="Specification 1 (format: key=value, leave empty to finish)")
            ]
            spec_answer = inquirer.prompt(questions)
            if spec_answer and spec_answer['spec1']:
                try:
                    key, value = spec_answer['spec1'].split('=', 1)
                    specs[key.strip()] = value.strip()
                except ValueError:
                    print("Invalid format. Skipping specifications.")
        
        # Add the component
        success, message = self.pc_builder.add_component(comp_name, comp_type, specs)
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")

    def view_existing_builds(self):
        """View all existing builds"""
        print("\n" + "="*50)
        print("📋 EXISTING BUILDS")
        print("="*50)
        
        builds = self.pc_builder.get_all_builds()
        if not builds:
            print("❌ No builds found in database!")
            return
            
        for build in builds:
            print(f"\n🏗️  Build: {build.name} (ID: {build.id})")
            print("-" * 30)
            
            # Get components for this build
            if build.components_list:
                components = self.pc_builder.get_components_by_ids(build.components_list)
                for comp in components:
                    specs_str = ", ".join([f"{k}: {v}" for k, v in comp.specs.items()])
                    print(f"  • {comp.type}: {comp.name} ({specs_str})")
            else:
                print("  • No components in this build")
        
        print("="*50)

    def build_pc_menu(self):
        """Build PC submenu with current selections and validation"""
        # Get component types from database, filter to core components only
        all_component_types = self.pc_builder.get_distinct_component_types()
        core_components = ["CPU", "GPU", "RAM", "Motherboard", "Storage"]
        component_types = [ct for ct in all_component_types if ct in core_components]
        
        if not component_types:
            component_types = core_components  # fallback
        
        while True:
            # Display current selections
            self.display_selected_components()
            
            # Create menu choices
            choices = []
            
            # Add component selection options
            for comp_type in component_types:
                status = "✅" if comp_type in self.selected_components else "⭕"
                choices.append((f"{status} Select {comp_type}", f"select_{comp_type}"))
            
            # Add other options
            choices.extend([
                ("✔️  Validate Current Build", "validate"),
                ("💾 Save Build", "save"),
                ("🔄 Clear All Selections", "clear"),
                ("⬅️  Back to Main Menu", "back")
            ])
            
            questions = [
                inquirer.List(
                    'action',
                    message="Build Your PC - What would you like to do?",
                    choices=choices,
                    carousel=True
                )
            ]
            
            answer = inquirer.prompt(questions)
            if not answer:
                break
                
            action = answer['action']
            
            if action.startswith('select_'):
                comp_type = action.replace('select_', '')
                component = self.select_component(comp_type)
                if component:
                    self.selected_components[comp_type] = component
                    print(f"\n✅ {comp_type} selected: {component.name}")
                    
                    # Auto-validate after each selection
                    if len(self.selected_components) > 1:
                        print("\n🔍 Running compatibility check...")
                        self.validate_build()
                    
                    input("\nPress Enter to continue...")
                    
            elif action == "validate":
                self.validate_build()
                input("\nPress Enter to continue...")
                
            elif action == "save":
                self.save_build_option()
                input("\nPress Enter to continue...")
                
            elif action == "clear":
                questions = [
                    inquirer.Confirm('confirm', 
                                   message="Are you sure you want to clear all selections?",
                                   default=False)
                ]
                confirm_answer = inquirer.prompt(questions)
                if confirm_answer and confirm_answer['confirm']:
                    self.selected_components.clear()
                    print("\n🗑️  All selections cleared!")
                    input("\nPress Enter to continue...")
                
            elif action == "back":
                break
    
    def main_menu(self):
        """Main menu for the CLI"""
        while True:
            choices = [
                ("🏗️  Build PC", "build_pc"),
                ("🔧 Insert New Component", "insert_component"),
                ("📋 View Existing Builds", "view_builds"),
                ("🚪 Exit", "exit")
            ]
            
            questions = [
                inquirer.List(
                    'action',
                    message="PC Build Configuration Tool - Main Menu",
                    choices=choices,
                    carousel=True
                )
            ]
            
            answer = inquirer.prompt(questions)
            if not answer:
                break
                
            action = answer['action']
            
            if action == "build_pc":
                self.build_pc_menu()
                    
            elif action == "insert_component":
                self.insert_component()
                input("\nPress Enter to continue...")
                
            elif action == "view_builds":
                self.view_existing_builds()
                input("\nPress Enter to continue...")
                
            elif action == "exit":
                break
        
        print("\n👋 Thank you for using PC Build Configuration Tool!")
        self.pc_builder.close_connection()
    
    def run(self):
        """Run the CLI application"""
        try:
            self.main_menu()
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            self.pc_builder.close_connection()
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            self.pc_builder.close_connection()
            sys.exit(1)

if __name__ == "__main__":
    cli = PCBuildCLI()
    cli.run()