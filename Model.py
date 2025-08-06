import os
import json
import pymysql
from dotenv import load_dotenv

load_dotenv()

class Component:
    def __init__(self, id=None, name=None, type=None, specs=None):
        self.id = id
        self.name = name
        self.type = type
        self.specs = specs if isinstance(specs, dict) else json.loads(specs) if specs else {}

class Build:
    def __init__(self, id=None, name=None, components_list=None):
        self.id = id
        self.name = name
        self.components_list = components_list if isinstance(components_list, list) else json.loads(components_list) if components_list else []

class PCBuilder:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect_to_db()

    def connect_to_db(self):
        """Establish database connection"""
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = int(os.getenv("DB_PORT"))
        DB_NAME = os.getenv("DB_NAME")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")

        self.connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        self.cursor = self.connection.cursor()

    def close_connection(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def get_component_by_id(self, component_id):
        """Get a single component by ID"""
        self.cursor.execute("SELECT id, name, type, specs FROM components WHERE id = %s", (component_id,))
        result = self.cursor.fetchone()
        if result:
            return Component(id=result[0], name=result[1], type=result[2], specs=result[3])
        return None

    def get_components_by_ids(self, component_ids):
        """Get multiple components by their IDs"""
        if not component_ids:
            return []
        
        placeholders = ','.join(['%s'] * len(component_ids))
        query = f"SELECT id, name, type, specs FROM components WHERE id IN ({placeholders})"
        self.cursor.execute(query, component_ids)
        results = self.cursor.fetchall()
        
        components = []
        for result in results:
            components.append(Component(id=result[0], name=result[1], type=result[2], specs=result[3]))
        return components

    def get_all_components(self):
        """Get all components from database"""
        self.cursor.execute("SELECT id, name, type, specs FROM components")
        results = self.cursor.fetchall()
        
        components = []
        for result in results:
            components.append(Component(id=result[0], name=result[1], type=result[2], specs=result[3]))
        return components

    def get_components_by_type(self, component_type):
        """Get components filtered by type"""
        self.cursor.execute("SELECT id, name, type, specs FROM components WHERE type = %s", (component_type,))
        results = self.cursor.fetchall()
        
        components = []
        for result in results:
            components.append(Component(id=result[0], name=result[1], type=result[2], specs=result[3]))
        return components

    def get_distinct_component_types(self):
        """Get all distinct component types from database"""
        self.cursor.execute("SELECT DISTINCT type FROM components ORDER BY type")
        results = self.cursor.fetchall()
        return [result[0] for result in results]

    def validate_compatibility(self, components):
        """Validate compatibility between components with comprehensive checks"""
        issues = []
        
        # Get components by type
        cpu = next((c for c in components if c.type == "CPU"), None)
        mobo = next((c for c in components if c.type == "Motherboard"), None)
        ram = next((c for c in components if c.type == "RAM"), None)
        gpu = next((c for c in components if c.type == "GPU"), None)
        storage = [c for c in components if c.type == "Storage"]
        
        # 1. CPU and Motherboard socket compatibility
        if cpu and mobo:
            cpu_socket = cpu.specs.get("socket", "").upper()
            mobo_socket = mobo.specs.get("socket", "").upper()
            if cpu_socket and mobo_socket and cpu_socket != mobo_socket:
                issues.append(f"CPU socket ({cpu_socket}) incompatible with Motherboard socket ({mobo_socket})")
        
        # 2. RAM and Motherboard compatibility
        if ram and mobo:
            ram_type = ram.specs.get("type", "").upper()
            mobo_ram_support = mobo.specs.get("ram_support", "").upper()
            if ram_type and mobo_ram_support:
                # Check if motherboard supports the RAM type
                if ram_type not in mobo_ram_support:
                    issues.append(f"RAM type ({ram_type}) not supported by Motherboard (supports: {mobo_ram_support})")
            
            # Check RAM speed compatibility
            ram_speed = ram.specs.get("speed", "")
            mobo_max_ram_speed = mobo.specs.get("max_ram_speed", "")
            if ram_speed and mobo_max_ram_speed:
                try:
                    ram_speed_num = int(ram_speed.replace("MHz", "").replace("MT/s", ""))
                    mobo_max_speed_num = int(mobo_max_ram_speed.replace("MHz", "").replace("MT/s", ""))
                    if ram_speed_num > mobo_max_speed_num:
                        issues.append(f"RAM speed ({ram_speed}) exceeds motherboard maximum ({mobo_max_ram_speed})")
                except (ValueError, AttributeError):
                    pass  # Skip if parsing fails
        
        # 3. GPU and Motherboard PCIe compatibility
        if gpu and mobo:
            gpu_interface = gpu.specs.get("interface", "").upper()
            mobo_pcie_support = mobo.specs.get("pcie_support", "").upper()
            if gpu_interface and mobo_pcie_support:
                # Check if motherboard supports PCIe
                if "PCIE" in gpu_interface and mobo_pcie_support != "YES":
                    issues.append(f"GPU requires PCIe support but motherboard PCIe support: {mobo_pcie_support}")
        
        # 4. Storage interface compatibility
        if storage and mobo:
            mobo_sata_support = mobo.specs.get("sata_support", "").upper()
            mobo_nvme_support = mobo.specs.get("nvme_support", "").upper()
            
            sata_drives = [s for s in storage if s.specs.get("interface", "").upper() == "SATA"]
            nvme_drives = [s for s in storage if s.specs.get("interface", "").upper() == "NVME"]
            
            if sata_drives and mobo_sata_support != "YES":
                issues.append(f"SATA storage selected but motherboard SATA support: {mobo_sata_support}")
            
            if nvme_drives and mobo_nvme_support != "YES":
                issues.append(f"NVMe storage selected but motherboard NVMe support: {mobo_nvme_support}")
        
        # Return results
        if issues:
            return False, "; ".join(issues)
        else:
            return True, "All components are compatible!"

    def save_build(self, name, component_ids):
        """Save a new build with compatibility validation"""
        try:
            # Get components by IDs
            components = self.get_components_by_ids(component_ids)
            
            if len(components) != len(component_ids):
                return False, "Some component IDs are invalid"
            
            # Validate compatibility
            valid, message = self.validate_compatibility(components)
            if not valid:
                return False, message

            # Save build to database
            self.cursor.execute(
                "INSERT INTO builds (name, components_list) VALUES (%s, %s)",
                (name, json.dumps(component_ids))
            )
            self.connection.commit()
            return True, f"Build '{name}' saved successfully"
            
        except Exception as e:
            self.connection.rollback()
            return False, f"Error saving build: {str(e)}"

    def get_build_by_id(self, build_id):
        """Get a build by ID"""
        self.cursor.execute("SELECT id, name, components_list FROM builds WHERE id = %s", (build_id,))
        result = self.cursor.fetchone()
        if result:
            return Build(id=result[0], name=result[1], components_list=result[2])
        return None

    def get_all_builds(self):
        """Get all builds from database"""
        self.cursor.execute("SELECT id, name, components_list FROM builds")
        results = self.cursor.fetchall()
        
        builds = []
        for result in results:
            builds.append(Build(id=result[0], name=result[1], components_list=result[2]))
        return builds

    def delete_build(self, build_id):
        """Delete a build by ID"""
        try:
            self.cursor.execute("DELETE FROM builds WHERE id = %s", (build_id,))
            if self.cursor.rowcount > 0:
                self.connection.commit()
                return True, "Build deleted successfully"
            else:
                return False, "Build not found"
        except Exception as e:
            self.connection.rollback()
            return False, f"Error deleting build: {str(e)}"

    def add_component(self, name, component_type, specs):
        """Add a new component to the database"""
        try:
            self.cursor.execute(
                "INSERT INTO components (name, type, specs) VALUES (%s, %s, %s)",
                (name, component_type, json.dumps(specs))
            )
            self.connection.commit()
            return True, f"Component '{name}' added successfully"
        except Exception as e:
            self.connection.rollback()
            return False, f"Error adding component: {str(e)}"


