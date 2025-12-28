import os
import json
import tempfile
import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash, send_file
from jinja2 import ChoiceLoader, PackageLoader
from werkzeug.utils import secure_filename
from certificate.certificate_cli import CertificateCLI
from certificate.cert_defines import *
import certificate.cert_utils as cert_utils
import common.web.web_utils as web_utils
import serial.tools.list_ports

# Certificate Run Defines
DATA_REAL_TAGS = "REAL"
DATA_SIMULATION = "SIM"
TEST_LIST_DEFAULT_FILE = "certificate_sanity_test_list.txt"
PREFERRED_TERMINAL = os.getenv("CLI_TERMINAL", "auto")
CERT_TESTS_ROOT = os.path.join(BASE_DIR, "tests")

# Module Names
MODULE_CLOUD_CONNECTIVITY = "cloud_connectivity"
MODULE_EDGE_MGMT = "edge_mgmt"

# Flavor constants
FLAVOR_GW_ONLY = "gw_only"
FLAVOR_BRIDGE_ONLY = "bridge_only"
FLAVOR_COMBO = "combo"

# Upload configuration - use system temp directory
TEMP_BASE = tempfile.gettempdir()
UPLOAD_FOLDER = os.path.join(TEMP_BASE, "wiliot_certificate_uploaded_schemas")
CONFIG_FOLDER = os.path.join(TEMP_BASE, "wiliot_certificate_saved_configs")
TEST_LIST_FOLDER = os.path.join(TEMP_BASE, "wiliot_certificate_test_lists")
CUSTOM_BROKER_FOLDER = os.path.join(TEMP_BASE, "wiliot_certificate_custom_brokers")
ALLOWED_EXTENSIONS = {'json'}
MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB

# Default custom broker configuration (from hivemq.json)
DEFAULT_CUSTOM_BROKER = {
    "port": 8883,
    "brokerUrl": "mqtts://broker.hivemq.com",
    "username": "",
    "password": "",
    "ownerId": "wiliot"
}

CUSTOM_BROKER_HELP = {
    "ownerId": "Used to construct topics, e.g.: data-v2/<ownerId>/<gatewayId>"
}

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for sessions
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONFIG_FOLDER, exist_ok=True)
os.makedirs(TEST_LIST_FOLDER, exist_ok=True)
os.makedirs(CUSTOM_BROKER_FOLDER, exist_ok=True)

# extend Jinja search path to include shared dir
app.jinja_loader = ChoiceLoader([
    app.jinja_loader,
    PackageLoader("common.web", "templates"),
])
# Update jinja_env globals
app.jinja_env.globals.update(
    FDM=web_utils.FDM,
    CERT_WEB=web_utils.CERT_WEB,
    **web_utils.GLOBAL_DEFINES_TO_UPDATE
)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_mandatory_modules_for_flavor(flavor):
    """Get mandatory modules for a given flavor."""
    if flavor == FLAVOR_GW_ONLY:
        return [MODULE_CLOUD_CONNECTIVITY]
    elif flavor == FLAVOR_BRIDGE_ONLY:
        return [MODULE_EDGE_MGMT]  # Interface module
    elif flavor == FLAVOR_COMBO:
        return [MODULE_CLOUD_CONNECTIVITY, MODULE_EDGE_MGMT]
    return []

def get_mandatory_modules_by_schema(schema_data, flavor):
    """Get modules that are mandatory by schema (modules declared in schema)."""
    if not schema_data or "modules" not in schema_data:
        return []
    
    # Only apply to bridge flavors (bridge_only and combo)
    if flavor not in (FLAVOR_BRIDGE_ONLY, FLAVOR_COMBO):
        return []
    
    schema_modules = schema_data.get("modules", {})
    if not isinstance(schema_modules, dict):
        return []
    
    # Map schema module names to test module names
    mandatory_by_schema = []
    for schema_mod_name in schema_modules.keys():
        # Map schema module name to test module name
        test_mod_name = test_module_and_schema_module_to_other(schema_mod_name)
        if test_mod_name not in mandatory_by_schema and test_mod_name != 'custom':
            mandatory_by_schema.append(test_mod_name)
    
    return mandatory_by_schema

# TODO: This is a temporary mapping to map test module names to schema module names - remove this
def test_module_and_schema_module_to_other(module_name):
    """Map test module names and schema module names to one another."""
    mapping = {
        "calibration": "calibration",
        "datapath": "datapath",
        "energy2400": "energy2400",
        "energy_sub1g": "energySub1g",  # snake_case to camelCase
        "pwr_mgmt": "powerManagement",  # abbreviated to full camelCase
        "sensors": "externalSensor",  # different name
        "custom": "custom"
    }
    for k, v in mapping.items():
        if module_name == k:
            return v
        if module_name == v:
            return k
    return module_name  # Return as-is if not in mapping

def filter_modules_by_flavor(tests_schema, flavor, schema_data=None):
    """Filter modules and tests based on selected flavor."""
    mandatory_modules = get_mandatory_modules_for_flavor(flavor)
    filtered_modules = []
    
    # Get schema module order if available
    schema_module_order = []
    if schema_data and "modules" in schema_data:
        schema_module_order = list(schema_data["modules"].keys())
    
    for mod in tests_schema.get("modules", []):
        mod_name = mod.get("name", "")
        filtered_tests = []
        
        for test in mod.get("tests", []):
            test_meta = test.get("meta", {})
            gw_only_test = test_meta.get("gwOnlyTest", 0)
            
            # Filter tests based on flavor
            if flavor == FLAVOR_GW_ONLY:
                # For GW only, include tests marked as gwOnlyTest or from cloud_connectivity module
                if gw_only_test == 1 or mod_name == MODULE_CLOUD_CONNECTIVITY:
                    filtered_tests.append(test)
            elif flavor == FLAVOR_BRIDGE_ONLY:
                # For Bridge only, exclude GW-only tests (but include all others)
                if gw_only_test == 0:
                    filtered_tests.append(test)
            elif flavor == FLAVOR_COMBO:
                # Include all tests for combo
                filtered_tests.append(test)
        
        # Get modules mandatory by schema
        mandatory_by_schema = get_mandatory_modules_by_schema(schema_data, flavor) if schema_data else []
        is_mandatory_by_schema = mod_name in mandatory_by_schema
        
        # Only include module if it has tests or is mandatory (by flavor or schema)
        # For mandatory modules, include even if no tests match (they'll be shown but empty)
        if filtered_tests or mod_name in mandatory_modules or is_mandatory_by_schema:
            mod_copy = mod.copy()
            mod_copy["tests"] = filtered_tests
            mod_copy["is_mandatory"] = mod_name in mandatory_modules
            mod_copy["is_mandatory_by_schema"] = is_mandatory_by_schema
            filtered_modules.append(mod_copy)
    
    # Sort modules: cloud_connectivity first, then edge_mgmt, then by schema order
    def module_sort_key(mod):
        mod_name = mod.get("name", "")
        # cloud_connectivity always first
        if mod_name == MODULE_CLOUD_CONNECTIVITY:
            return (0, "")
        # edge_mgmt always first among bridge modules
        if mod_name == MODULE_EDGE_MGMT:
            return (1, "")
        # Then modules in schema order
        if schema_module_order:
            try:
                # Map test module name to schema module name
                schema_mod_name = test_module_and_schema_module_to_other(mod_name)
                idx = schema_module_order.index(schema_mod_name)
                return (2, idx)
            except ValueError:
                pass
        return (3, mod_name)
    
    filtered_modules.sort(key=module_sort_key)
    
    return filtered_modules

def get_mandatory_tests_for_modules(modules):
    """Get list of mandatory test IDs from selected modules."""
    mandatory_tests = []
    for mod in modules:
        for test in mod.get("tests", []):
            if test.get("meta", {}).get("mandatory", 0) == 1:
                mandatory_tests.append(test.get("id"))
    return mandatory_tests

def _check_missing_defaults(properties, path_prefix=""):
    """
    Recursively check if all properties have default values.
    Returns list of field paths missing defaults.
    Properties with nested 'properties' (object types) don't need defaults themselves,
    only their nested properties need defaults.
    Array types with 'items' field also don't need defaults.
    """
    missing_defaults = []
    
    if not isinstance(properties, dict):
        return missing_defaults
    
    for field_name, field_def in properties.items():
        if not isinstance(field_def, dict):
            continue
            
        current_path = f"{path_prefix}.{field_name}" if path_prefix else field_name
        
        # Check if this field has nested properties
        has_nested_properties = "properties" in field_def and isinstance(field_def["properties"], dict)
        
        # Check if this is an array type with items
        is_array_with_items = field_def.get("type") == "array" and "items" in field_def
        
        # Only check for default if this property doesn't have nested properties and isn't an array with items
        # (Objects with nested properties and arrays with items don't need defaults themselves)
        if not has_nested_properties and not is_array_with_items and "default" not in field_def:
            missing_defaults.append(current_path)
        
        # Recursively check nested properties if they exist
        if has_nested_properties:
            nested_missing = _check_missing_defaults(field_def["properties"], current_path)
            missing_defaults.extend(nested_missing)
    
    return missing_defaults

def validate_schema_file(filepath):
    """Validate the uploaded schema file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Basic validation
        if "properties" not in data and "modules" not in data:
            return False, "Schema missing both 'properties' and 'modules' keys"
        
        # Check for cloud_connectivity_flag or brg_flag
        has_cloud = cert_utils.cloud_connectivity_flag(data)
        has_brg = cert_utils.brg_flag(data)
        
        if not (has_cloud or has_brg):
            return False, "Schema must support either cloud connectivity or bridge device"
        
        # Check for missing defaults in all fields
        missing_defaults = []
        
        # Check top-level properties (gateway properties)
        if "properties" in data and isinstance(data["properties"], dict):
            missing_defaults.extend(_check_missing_defaults(data["properties"], ""))
        
        # Check module properties (bridge modules)
        if "modules" in data and isinstance(data["modules"], dict):
            for module_name, module_def in data["modules"].items():
                if isinstance(module_def, dict) and "properties" in module_def:
                    module_missing = _check_missing_defaults(module_def["properties"], f"modules.{module_name}")
                    missing_defaults.extend(module_missing)
        
        if missing_defaults:
            # Format error message with clear list of missing fields
            if len(missing_defaults) == 1:
                return False, f"Field '{missing_defaults[0]}' is missing a 'default' value"
            else:
                missing_list = ", ".join(missing_defaults)
                return False, f"The following {len(missing_defaults)} fields are missing 'default' values: {missing_list}"
        
        return True, data
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def load_schema_data(schema_path):
    """Load schema data from file path. Returns None if file doesn't exist or can't be read."""
    if not schema_path:
        return None
    try:
        schema_path = os.path.normpath(str(schema_path).strip().strip('"').strip("'"))
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def verify_schema_matches_selection(schema_data, flavor, selected_modules, selected_tests):
    """Verify that the validation schema matches the selected flavor/modules/tests."""
    errors = []
    warnings = []
    
    has_cloud = cert_utils.cloud_connectivity_flag(schema_data)
    has_brg = cert_utils.brg_flag(schema_data)
    
    # Check flavor compatibility
    if flavor == FLAVOR_GW_ONLY and not has_cloud:
        errors.append("Schema does not support Gateway (cloud connectivity) but GW only flavor selected")
    elif flavor == FLAVOR_BRIDGE_ONLY and not has_brg:
        errors.append("Schema does not support Bridge but Bridge only flavor selected")
    elif flavor == FLAVOR_COMBO:
        if not has_cloud and not has_brg:
            errors.append("Schema does not support Gateway or Bridge for Combo flavor")
        elif not has_cloud:
            warnings.append("Schema missing Gateway support for Combo flavor")
        elif not has_brg:
            warnings.append("Schema missing Bridge support for Combo flavor")
    
    # Check module support (if schema has modules field)
    # The schema modules dict contains the bridge modules that the device supports
    # Note: cloud_connectivity is a gateway feature, not a bridge module, so it won't be in schema modules
    # Note: edge_mgmt is not a configurable module in schema
    # Only check bridge modules that are configurable in the schema
    if has_brg and "modules" in schema_data:
        schema_modules = schema_data.get("modules", {})
        if isinstance(schema_modules, dict):
            schema_module_names = set(schema_modules.keys())
            # Only check bridge modules that are configurable (exclude edge_mgmt and cloud_connectivity)
            bridge_modules_to_check = [m for m in selected_modules if m not in (MODULE_CLOUD_CONNECTIVITY, MODULE_EDGE_MGMT)]
            for test_mod_name in bridge_modules_to_check:
                # Map test module name to schema module name
                schema_mod_name = test_module_and_schema_module_to_other(test_mod_name)
                if schema_mod_name not in schema_module_names:
                    warnings.append(f"Module '{test_mod_name}' may not be supported according to the uploaded schema")
    
    return len(errors) == 0, errors, warnings

def check_certification_status(flavor, selected_modules, selected_tests, tests_schema, schema_data=None, unsterile_run=False):
    """Check if the selection qualifies for certification or is test-only."""
    mandatory_modules = get_mandatory_modules_for_flavor(flavor)
    mandatory_by_schema = get_mandatory_modules_by_schema(schema_data, flavor) if schema_data else []
    all_mandatory_tests = []
    
    # Get selected module names (handle both dict and string formats)
    selected_module_names = [m.get("name") if isinstance(m, dict) else m for m in selected_modules]
    
    # Get all mandatory tests from ALL selected modules (not just mandatory modules)
    # When a module is selected, its mandatory tests become mandatory
    for mod in tests_schema.get("modules", []):
        mod_name = mod.get("name", "")
        if mod_name in selected_module_names:
            for test in mod.get("tests", []):
                if test.get("meta", {}).get("mandatory", 0) == 1:
                    all_mandatory_tests.append(test.get("id"))
    
    # Check if all mandatory modules are selected
    missing_modules = [m for m in mandatory_modules if m not in selected_module_names]
    
    # Check if all schema-mandatory modules are selected
    missing_modules_by_schema = [m for m in mandatory_by_schema if m not in selected_module_names]
    
    # Check if all mandatory tests (from selected modules) are selected
    missing_tests = [t for t in all_mandatory_tests if t not in selected_tests]
    
    # Check for "at least one additional module" requirement for Bridge Only and Combo
    missing_additional_module = False
    if flavor in (FLAVOR_BRIDGE_ONLY, FLAVOR_COMBO):
        # Count non-mandatory selected modules (exclude cloud_connectivity and edge_mgmt)
        additional_modules = [m for m in selected_module_names if m not in (MODULE_CLOUD_CONNECTIVITY, MODULE_EDGE_MGMT)]
        if len(additional_modules) == 0:
            missing_additional_module = True
    
    # A certifying run must be sterile - if unsterile_run is set, force non-certifying
    is_certified = (len(missing_modules) == 0 and len(missing_modules_by_schema) == 0 and 
                   len(missing_tests) == 0 and not missing_additional_module and not unsterile_run)
    
    return is_certified, missing_modules, missing_tests, missing_additional_module, missing_modules_by_schema

def _prepare_form_data_for_template(session, cert_schema):
    """Prepare form_data for template, ensuring custom_broker_path is included if available."""
    form_data = session.get('form_data', {}).copy()
    custom_broker_path = session.get('custom_broker_path')
    if custom_broker_path:
        custom_broker_field_name = f"{cert_schema['title']}_custom_broker"
        if custom_broker_field_name not in form_data:
            form_data[custom_broker_field_name] = custom_broker_path
    return form_data

def form_to_argv(form, parser, title) -> list[str]:
    """
    Map POSTed form fields back into argv tokens the parser expects.
    - For flags (store_true/false): include the flag when checked.
    - For text/select: include '--opt value' only if non-empty (keeps defaults otherwise).
    - Special-case overwrite_defaults: accept textarea of key=value lines -> join to key=value,... string.
    """
    argv: list[str] = []
    for a in parser._actions:
        from argparse import _HelpAction, _VersionAction, _StoreTrueAction, _StoreFalseAction
        if isinstance(a, (_HelpAction, _VersionAction)) or a.dest in ('tl', 'validation_schema'):
            continue

        dest = f'{title}_{a.dest}'
        opt = a.option_strings and max(a.option_strings, key=len)  # prefer long option
        val = form.get(dest, "")

        # Special handling: overwrite_defaults textarea to csv string
        if "overwrite_defaults" in dest:
            # allow either CSV or line-per-pair; normalize to CSV for parser type fn
            lines = [ln.strip().replace(" ", "") for ln in form.get(dest, "").splitlines() if ln.strip()]
            if lines:
                val = ",".join(lines)

        if getattr(a, "choices", None) and a.nargs in ("+", "*"):
            vals = form.getlist(dest + "[]")
            if vals:
                argv += [opt] + vals
            continue

        # store_true / store_false
        if isinstance(a, _StoreTrueAction):
            if form.get(dest):  # checkbox "on"
                argv += [opt]
            continue
        if isinstance(a, _StoreFalseAction):
            if form.get(dest):
                argv += [opt]
            continue

        # Positionals (you have none) vs optionals (you have only optionals)
        if a.option_strings:
            if val not in ("", None):
                argv += [opt, val]
        else:
            if val not in ("", None):
                argv += [val]
    return argv

def _sort_tests_by_module_priority(test_ids: list[str]) -> list[str]:
    """
    Sort test IDs to ensure edge_mgmt tests come first (after cloud_connectivity if present).
    Test ID format: 'module/test_name'
    """
    def test_sort_key(test_id: str):
        module, _, test_name = test_id.partition('/')
        # Connection test first (requires manual unplug and replug)
        if module == MODULE_CLOUD_CONNECTIVITY and "connection" in test_name.lower():
            return (0, test_id)
        # other cloud_connectivity tests
        if module == MODULE_CLOUD_CONNECTIVITY:
            return (1, test_id)
        # edge_mgmt second
        if module == MODULE_EDGE_MGMT:
            return (2, test_id)
        # Others last
        return (3, test_id)
    
    return sorted(test_ids, key=test_sort_key)

def _write_testlist(selected_ids: list[str], form_data=None, is_certified=False) -> str:
    """
    Create a temp test list file in the temp directory. If your CLI expects script paths, write id_to_py[tid].
    If it expects logical names, write 'module/test'. Adjust once here.
    """
    # Sort tests to ensure edge_mgmt comes first
    sorted_test_ids = _sort_tests_by_module_priority(selected_ids)
    
    test_list = f"custom_tl_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"
    path = os.path.join(TEST_LIST_FOLDER, test_list)
    with open(path, 'w') as f:
        # Add comment about certification status
        if not is_certified:
            f.write("# NON-CERTIFYING RUN (mandatory tests/modules missing)\n")
        for test_id in sorted_test_ids:
            tid_safe = test_id.replace('/', '_')
            # Check for dynamic parameter first (non-array format)
            dynamic_param_key = f"params_{tid_safe}_dynamic"
            dynamic_param = form_data.get(dynamic_param_key) if form_data else None
            
            if dynamic_param is not None and dynamic_param != "":
                # Use dynamic parameter value
                params = [str(dynamic_param)]
            else:
                # Use regular parameter array
                param_key = f"params_{tid_safe}[]"
                params = form_data.getlist(param_key) if form_data else []  # list[str]
            # Example line format: "<module/test> <param1> <param2> ..."
            line = " ".join([test_id] + params)
            f.write(line + "\n")
    print(f"Custom test list saved in {path}")
    return path

def _write_custom_broker_config(form_data, cert_schema_title="cert_run") -> str:
    """
    Generate a custom broker JSON configuration file from form data.
    Extracts broker field values and creates a JSON file matching hivemq.json format.
    """
    # Extract broker configuration from form_data
    broker_config = {}
    
    # Field names follow pattern: {schema_title}_custom_broker_{field_name}
    field_prefix = f"{cert_schema_title}_custom_broker_"
    
    # Extract values from form_data, using defaults if not provided
    for field in DEFAULT_CUSTOM_BROKER.keys():
        field_name = f"{field_prefix}{field}"
        value = form_data.get(field_name, "")
        
        if field == "port":
            # Convert port to int if it's a number
            try:
                broker_config[field] = int(value) if value else DEFAULT_CUSTOM_BROKER[field]
            except (ValueError, TypeError):
                broker_config[field] = DEFAULT_CUSTOM_BROKER[field]
        elif field == "ownerId":
            # Convert ownerId to topics
            broker_config[CUSTOM_BROKER_UPDATE_TOPIC] = f'update/{value}/<{GW_ID}>'
            broker_config[CUSTOM_BROKER_DATA_TOPIC] = f'data/{value}/<{GW_ID}>'
            broker_config[CUSTOM_BROKER_STATUS_TOPIC] = f'status/{value}/<{GW_ID}>'
        else:
            broker_config[field] = value
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_broker_{timestamp}.json"
    filepath = os.path.join(CUSTOM_BROKER_FOLDER, filename)
    
    # Write JSON file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(broker_config, f, indent=4)
    
    print(f"Custom broker config saved in {filepath}")
    return filepath

@app.route("/")
def index():
    """Redirect to step 1 or show current step."""
    if 'current_step' not in session:
        session['current_step'] = 1
        session['flavor'] = None
        session['schema_path'] = None
        session['selected_modules'] = []
        session['selected_tests'] = []
        session['form_data'] = {}
    return redirect(url_for('step', step_num=session.get('current_step', 1)))

@app.route("/step/<int:step_num>", methods=['GET', 'POST'])
def step(step_num):
    """Handle multi-step wizard navigation."""
    if step_num < 1 or step_num > 5:
        flash("Invalid step number", "error")
        return redirect(url_for('index'))
    
    # Initialize session if needed
    if 'current_step' not in session:
        session['current_step'] = 1
        session['flavor'] = None
        session['schema_path'] = None
        session['selected_modules'] = []
        session['selected_tests'] = []
        session['form_data'] = {}
        session['schema_mandatory_initialized'] = False
    
    title = "Run Certificate"
    tests_schema = web_utils.scan_tests_dir(CERT_TESTS_ROOT)
    error = None
    warning = None
    
    if request.method == "POST":
        action = request.form.get('action', 'next')
        
        if action == 'back':
            # For GW only, skip step 3 when going back from step 4
            if step_num == 4 and session.get('flavor') == FLAVOR_GW_ONLY:
                session['current_step'] = 2
            else:
                session['current_step'] = max(1, step_num - 1)
            return redirect(url_for('step', step_num=session['current_step']))
        
        # Step 1: Flavor selection
        if step_num == 1:
            flavor = request.form.get('flavor')
            if flavor in [FLAVOR_GW_ONLY, FLAVOR_BRIDGE_ONLY, FLAVOR_COMBO]:
                session['flavor'] = flavor
                # Initialize mandatory modules only if not already set (preserves user selections)
                if 'selected_modules' not in session or not session.get('selected_modules'):
                    mandatory_modules = get_mandatory_modules_for_flavor(flavor)
                    session['selected_modules'] = mandatory_modules
                session['current_step'] = 2
                return redirect(url_for('step', step_num=2))
            else:
                error = "Please select a flavor"
        
        # Step 2: Validation schema upload
        elif step_num == 2:
            # Only validate file if moving forward (not going back)
            if action == 'next':
                if 'schema_file' in request.files:
                    file = request.files['schema_file']
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{timestamp}_{filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        is_valid, result = validate_schema_file(filepath)
                        if is_valid:
                            # Store normalized path without quotes (don't store full schema_data to avoid cookie size issues)
                            normalized_path = os.path.normpath(filepath)
                            session['schema_path'] = normalized_path
                            # Don't store schema_data in session - load from file when needed
                            # Initialize mandatory modules only if not already set (preserves user selections)
                            flavor = session.get('flavor')
                            if 'selected_modules' not in session or not session.get('selected_modules'):
                                mandatory_modules = get_mandatory_modules_for_flavor(flavor)
                                # Add schema-mandatory modules
                                schema_data = result  # result is the validated schema data
                                mandatory_by_schema = get_mandatory_modules_by_schema(schema_data, flavor)
                                all_mandatory = list(set(mandatory_modules + mandatory_by_schema))
                                session['selected_modules'] = all_mandatory
                                # Mark schema-mandatory modules as initialized
                                session['schema_mandatory_initialized'] = True
                            else:
                                # If modules already exist, add schema-mandatory modules and mark as initialized
                                schema_data = result
                                mandatory_by_schema = get_mandatory_modules_by_schema(schema_data, flavor)
                                current_modules = session.get('selected_modules', [])
                                updated_modules = list(set(current_modules + mandatory_by_schema))
                                if len(updated_modules) > len(current_modules):
                                    session['selected_modules'] = updated_modules
                                session['schema_mandatory_initialized'] = True
                            # For GW only, skip step 3 (modules)
                            if session.get('flavor') == FLAVOR_GW_ONLY:
                                session['current_step'] = 4
                                return redirect(url_for('step', step_num=4))
                            else:
                                session['current_step'] = 3
                                return redirect(url_for('step', step_num=3))
                        else:
                            error = f"Schema validation failed: {result}"
                            os.remove(filepath)
                    else:
                        error = "Please upload a valid JSON schema file"
                else:
                    error = "Please select a validation schema file"
        
        # Step 3: Module selection
        elif step_num == 3:
            # Skip step 3 for GW only (shouldn't reach here, but handle gracefully)
            if session.get('flavor') == FLAVOR_GW_ONLY:
                mandatory_modules = get_mandatory_modules_for_flavor(FLAVOR_GW_ONLY)
                session['selected_modules'] = mandatory_modules
                session['current_step'] = 4
                return redirect(url_for('step', step_num=4))
            
            selected_modules = request.form.getlist('modules[]')
            
            # Get mandatory modules for this flavor
            flavor = session.get('flavor')
            mandatory_modules = get_mandatory_modules_for_flavor(flavor) if flavor else []
            
            # Use submitted modules directly (mandatory modules can now be deselected)
            all_selected_modules = selected_modules
            
            # Allow moving forward even if requirements aren't met (warnings shown via JavaScript)
            if all_selected_modules:
                session['selected_modules'] = all_selected_modules
            session['current_step'] = 4
            return redirect(url_for('step', step_num=4))
        
        # Step 4: Test selection
        elif step_num == 4:
            selected_tests = request.form.getlist('tests[]')
            
            # Get mandatory tests from selected modules
            flavor = session.get('flavor')
            selected_modules = session.get('selected_modules', [])
            schema_path = session.get('schema_path')
            schema_data = load_schema_data(schema_path) if schema_path else None
            filtered_modules = filter_modules_by_flavor(tests_schema, flavor, schema_data) if flavor else []
            
            # Find all mandatory tests from selected modules
            mandatory_tests = []
            for mod in filtered_modules:
                if mod.get('name') in selected_modules:
                    for test in mod.get('tests', []):
                        if test.get('meta', {}).get('mandatory', 0) == 1:
                            mandatory_tests.append(test.get('id'))
            
            # Use submitted tests directly (mandatory tests can now be deselected)
            all_selected_tests = selected_tests
            
            # Store all form data including CLI parameters and test parameters
            form_data_dict = {}
            for key in request.form:
                if key.endswith('[]'):
                    form_data_dict[key] = request.form.getlist(key)
                else:
                    form_data_dict[key] = request.form.get(key)
            
            # Handle custom_broker configuration from form fields
            cert_cli = CertificateCLI()
            cert_schema = web_utils.parser_to_schema(cert_cli.parser)
            custom_broker_field_name = f"{cert_schema['title']}_custom_broker"
            
            # Generate custom broker JSON file from form fields
            try:
                broker_config_path = _write_custom_broker_config(form_data_dict, cert_schema['title'])
                normalized_path = os.path.normpath(broker_config_path)
                session['custom_broker_path'] = normalized_path
                form_data_dict[custom_broker_field_name] = normalized_path
            except Exception as e:
                error = f"Error generating custom broker configuration: {e}"
            
            # Validate all required fields (required for moving forward, but allow going back)
            if action == 'next':
                # Get required fields from CLI schema
                cert_cli = CertificateCLI()
                cert_schema = web_utils.parser_to_schema(cert_cli.parser)
                required_fields = []
                missing_required = []
                
                # Find all required fields (excluding validation_schema and tl which are handled separately)
                for field in cert_schema.get('fields', []):
                    if field.get('required') and field.get('name') not in ('validation_schema', 'tl'):
                        required_fields.append(field)
                
                # Check each required field
                for field in required_fields:
                    field_name = f"{cert_schema['title']}_{field['name']}"
                    field_value = form_data_dict.get(field_name, '')
                    
                    # Special handling for custom_broker - check if all required broker fields are filled
                    if field['name'] == 'custom_broker':
                        # Check all broker fields except username and password are filled
                        broker_field_prefix = f"{cert_schema['title']}_custom_broker_"
                        optional_fields = {'username', 'password'}
                        for broker_field_key in DEFAULT_CUSTOM_BROKER.keys():
                            if broker_field_key not in optional_fields:
                                broker_field_name = f"{broker_field_prefix}{broker_field_key}"
                                broker_field_value = form_data_dict.get(broker_field_name, '')
                                if not broker_field_value or (isinstance(broker_field_value, str) and not broker_field_value.strip()):
                                    missing_required.append(f"custom_broker.{broker_field_key}")
                                    break
                        # Also check if path was generated (should be generated above if fields are valid)
                        if not field_value and not session.get('custom_broker_path'):
                            # Only add if we haven't already added a broker field error
                            if not any('custom_broker.' in req for req in missing_required):
                                missing_required.append(field.get('name', field['label']))
                    else:
                        # For other fields, check if value is provided
                        if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                            missing_required.append(field.get('name', field['label']))
                
                if missing_required:
                    if len(missing_required) == 1:
                        error = f"Please provide {missing_required[0]} to continue"
                    else:
                        error = f"Please provide the following required fields to continue: {', '.join(missing_required)}"
                else:
                    # Only save and move forward if all required fields are provided
                    if all_selected_tests:
                        session['selected_tests'] = all_selected_tests
                    session['form_data'] = form_data_dict
                    session['current_step'] = 5
                    return redirect(url_for('step', step_num=5))
            else:
                # Going back - save form data but don't validate required fields
                if all_selected_tests:
                    session['selected_tests'] = all_selected_tests
                session['form_data'] = form_data_dict
        
        # Step 5: Review and run
        elif step_num == 5:
            if request.form.get('action') == 'run':
                return execute_certificate()
            elif request.form.get('action') == 'edit':
                edit_step = int(request.form.get('edit_step', 1))
                session['current_step'] = edit_step
                return redirect(url_for('step', step_num=edit_step))
    
    # Prepare data for template
    flavor = session.get('flavor')
    schema_path = session.get('schema_path')
    selected_modules = session.get('selected_modules', [])
    selected_tests = session.get('selected_tests', [])
    
    # Initialize mandatory items only if not already in session (new session or after "Start New Run")
    # This ensures mandatory items are only pre-checked at the beginning
    if flavor and not selected_modules:
        mandatory_modules = get_mandatory_modules_for_flavor(flavor)
        # Add schema-mandatory modules if schema is available
        schema_data = load_schema_data(schema_path) if schema_path else None
        mandatory_by_schema = get_mandatory_modules_by_schema(schema_data, flavor) if schema_data else []
        all_mandatory = list(set(mandatory_modules + mandatory_by_schema))
        selected_modules = all_mandatory
        session['selected_modules'] = selected_modules
    
    # Ensure schema-mandatory modules are added when first reaching step 3 (only if not already initialized)
    # Use a session flag to track if schema-mandatory modules have been initialized
    if step_num == 3 and flavor and schema_path:
        schema_mandatory_initialized = session.get('schema_mandatory_initialized', False)
        if not schema_mandatory_initialized:
            schema_data = load_schema_data(schema_path) if schema_path else None
            if schema_data:
                mandatory_by_schema = get_mandatory_modules_by_schema(schema_data, flavor)
                # Add schema-mandatory modules that aren't already selected
                current_modules = session.get('selected_modules', [])
                updated_modules = list(set(current_modules + mandatory_by_schema))
                if len(updated_modules) > len(current_modules):
                    selected_modules = updated_modules
                    session['selected_modules'] = selected_modules
                # Mark as initialized so we don't re-add them when going back
                session['schema_mandatory_initialized'] = True
    
    # Initialize mandatory tests only if not already in session and we have selected modules
    # Only initialize when first reaching step 4 (not on every GET request)
    if flavor and selected_modules and not selected_tests and step_num == 4:
        schema_path = session.get('schema_path')
        schema_data = load_schema_data(schema_path) if schema_path else None
        filtered_modules = filter_modules_by_flavor(tests_schema, flavor, schema_data) if flavor else []
        mandatory_tests = []
        for mod in filtered_modules:
            if mod.get('name') in selected_modules:
                for test in mod.get('tests', []):
                    if test.get('meta', {}).get('mandatory', 0) == 1:
                        mandatory_tests.append(test.get('id'))
        if mandatory_tests:
            selected_tests = mandatory_tests
            session['selected_tests'] = selected_tests
    
    # Skip step 3 for GW only - redirect to step 4 if trying to access step 3
    if step_num == 3 and flavor == FLAVOR_GW_ONLY:
        if not selected_modules:
            mandatory_modules = get_mandatory_modules_for_flavor(FLAVOR_GW_ONLY)
            session['selected_modules'] = mandatory_modules
        return redirect(url_for('step', step_num=4))
    
    # Filter modules/tests based on flavor
    filtered_modules = []
    if flavor:
        schema_path = session.get('schema_path')
        schema_data = load_schema_data(schema_path) if schema_path else None
        filtered_modules = filter_modules_by_flavor(tests_schema, flavor, schema_data)
    
    # Get CLI schemas for form fields - use certificate_cli for all flavors (needed early for unsterile_run check)
    cert_cli = CertificateCLI()
    cert_schema = web_utils.parser_to_schema(cert_cli.parser)
    
    # Check if unsterile_run is set in form_data
    form_data = _prepare_form_data_for_template(session, cert_schema)
    unsterile_run_field = f"{cert_schema['title']}_unsterile_run"
    unsterile_run = bool(form_data.get(unsterile_run_field))
    
    # Get certification status
    is_certified = True
    missing_modules = []
    missing_tests = []
    missing_tests_details = []  # List of dicts with test id and label
    missing_additional_module = False
    missing_modules_by_schema = []
    if step_num >= 4 and flavor and selected_modules and selected_tests:
        # Convert selected_modules to module dicts for check_certification_status
        module_dicts = [m for m in filtered_modules if m.get('name') in selected_modules]
        schema_data = load_schema_data(schema_path) if schema_path else None
        is_certified, missing_modules, missing_tests, missing_additional_module, missing_modules_by_schema = check_certification_status(
            flavor, module_dicts, selected_tests, tests_schema, schema_data, unsterile_run
        )
        
        # Get test details (labels) for missing tests
        if missing_tests:
            for mod in filtered_modules:
                for test in mod.get('tests', []):
                    test_id = test.get('id')
                    if test_id in missing_tests:
                        missing_tests_details.append({
                            'id': test_id,
                            'label': test.get('label', test_id),
                            'module': mod.get('name', '')
                        })
    
    # Schema verification
    schema_errors = []
    schema_warnings = []
    if step_num == 5 and schema_path and flavor:
        schema_data = load_schema_data(schema_path)
        if schema_data:
            module_dicts = [m for m in filtered_modules if m.get('name') in selected_modules]
            is_valid, errors, warnings = verify_schema_matches_selection(
                schema_data, flavor, selected_modules, selected_tests
            )
            schema_errors = errors
            schema_warnings = warnings
            # Get missing schema-mandatory modules for display (recalculate if not already set)
            if not missing_modules_by_schema and step_num >= 4 and flavor and selected_modules:
                _, _, _, _, missing_modules_by_schema = check_certification_status(
                    flavor, module_dicts, selected_tests, tests_schema, schema_data, unsterile_run
                )
    
    
    # Calculate total test count including mandatory tests from selected modules
    total_test_count = len(selected_tests)
    if step_num >= 4 and flavor and selected_modules:
        # Find all mandatory tests from selected modules that might not be in selected_tests
        for mod in filtered_modules:
            if mod.get('name') in selected_modules:
                for test in mod.get('tests', []):
                    test_id = test.get('id')
                    if test.get('meta', {}).get('mandatory', 0) == 1 and test_id not in selected_tests:
                        total_test_count += 1
    
    # Prepare data for JavaScript validation
    # Always initialize these to avoid Undefined errors in template
    mandatory_modules_for_js = get_mandatory_modules_for_flavor(flavor) if flavor else []
    schema_data_for_js = load_schema_data(schema_path) if schema_path else None
    mandatory_modules_by_schema_for_js = get_mandatory_modules_by_schema(schema_data_for_js, flavor) if (schema_data_for_js and flavor) else []
    mandatory_tests_for_js = []
    
    if step_num in [3, 4] and flavor:
        if step_num == 4 and selected_modules:
            # For step 4, only include mandatory tests from selected modules
            for mod in filtered_modules:
                if mod.get('name') in selected_modules:
                    for test in mod.get('tests', []):
                        if test.get('meta', {}).get('mandatory', 0) == 1:
                            mandatory_tests_for_js.append({
                                'id': test.get('id'),
                                'label': test.get('label', test.get('id')),
                                'module': mod.get('name', '')
                            })
        elif step_num == 3:
            # For step 3, include all mandatory tests from all modules (for validation)
            for mod in filtered_modules:
                for test in mod.get('tests', []):
                    if test.get('meta', {}).get('mandatory', 0) == 1:
                        mandatory_tests_for_js.append({
                            'id': test.get('id'),
                            'label': test.get('label', test.get('id')),
                            'module': mod.get('name', '')
                        })
    
    # Get run completion info before clearing (for modal display)
    run_completed = session.get('run_completed', False)
    run_terminal = session.get('run_terminal')
    run_pid = session.get('run_pid')
    run_is_certified = session.get('run_is_certified')
    
    # Clear run flags after getting them (so modal only shows once)
    if run_completed:
        session.pop('run_completed', None)
        session.pop('run_terminal', None)
        session.pop('run_pid', None)
        session.pop('run_is_certified', None)
    
    # Get available COM ports for port dropdown
    available_ports = []
    try:
        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            available_ports.append({
                'value': port,
                'label': f"{port}: {desc} [{hwid}]"
            })
    except Exception:
        # If serial tools are not available, leave empty list
        pass
    
    return render_template('cert_run.html',
                           app=web_utils.CERT_WEB,
                           title=title,
                           step_num=step_num,
                           flavor=flavor,
                           schema_path=schema_path,
                           selected_modules=selected_modules,
                           selected_tests=selected_tests,
                           total_test_count=total_test_count,
                           filtered_modules=filtered_modules,
                           tests_schema=tests_schema,
                           cert_schema=cert_schema,
                           is_certified=is_certified,
                           missing_modules=missing_modules,
                           missing_tests=missing_tests,
                           missing_tests_details=missing_tests_details,
                           missing_additional_module=missing_additional_module,
                           schema_errors=schema_errors,
                           schema_warnings=schema_warnings,
                           missing_modules_by_schema=missing_modules_by_schema,
                           mandatory_modules_for_js=mandatory_modules_for_js,
                           mandatory_modules_by_schema_for_js=mandatory_modules_by_schema_for_js,
                           mandatory_tests_for_js=mandatory_tests_for_js,
                           error=error,
                           warning=warning,
                           form_data=_prepare_form_data_for_template(session, cert_schema),
                           custom_broker_defaults=DEFAULT_CUSTOM_BROKER,
                           custom_broker_help=CUSTOM_BROKER_HELP,
                           custom_broker_field_keys=list(DEFAULT_CUSTOM_BROKER.keys()),
                           run_completed=run_completed,
                           run_terminal=run_terminal,
                           run_pid=run_pid,
                           run_is_certified=run_is_certified,
                           available_ports=available_ports,
                           unsterile_run=unsterile_run)

def execute_certificate():
    """Execute the certificate run based on session data."""
    flavor = session.get('flavor')
    schema_path = session.get('schema_path')
    selected_tests = session.get('selected_tests', [])
    form_data = session.get('form_data', {})
    
    if not flavor or not schema_path or not selected_tests:
        flash("Missing required information. Please start over.", "error")
        return redirect(url_for('step', step_num=1))
    
    # Strip any quotes that might have been added and normalize path
    schema_path = str(schema_path).strip().strip('"').strip("'")
    schema_path = os.path.normpath(schema_path)
    
    # Verify schema file exists
    if not os.path.exists(schema_path):
        flash(f"Validation schema file not found: {schema_path}", "error")
        return redirect(url_for('step', step_num=2))
    
    # Check certification status
    tests_schema = web_utils.scan_tests_dir(CERT_TESTS_ROOT)
    filtered_modules = filter_modules_by_flavor(tests_schema, flavor)
    module_dicts = [m for m in filtered_modules if m.get('name') in session.get('selected_modules', [])]
    schema_data = load_schema_data(schema_path) if schema_path else None
    # Check if unsterile_run is set in form_data
    cert_cli = CertificateCLI()
    cert_schema = web_utils.parser_to_schema(cert_cli.parser)
    unsterile_run_field = f"{cert_schema['title']}_unsterile_run"
    unsterile_run = bool(form_data.get(unsterile_run_field))
    is_certified, _, _, _, _ = check_certification_status(flavor, module_dicts, selected_tests, tests_schema, schema_data, unsterile_run)
    
    full_cmd = []
    
    # Create a request-like object for form_to_argv
    class FormDict:
        def __init__(self, data):
            self.data = data
        def get(self, key, default=""):
            return self.data.get(key, default)
        def getlist(self, key):
            val = self.data.get(key)
            if isinstance(val, list):
                return val
            elif val:
                return [val]
            else:
                return []
    
    # Ensure custom_broker_path from session is in form_data if available
    custom_broker_path = session.get('custom_broker_path')
    if custom_broker_path and custom_broker_path not in form_data.values():
        cert_cli = CertificateCLI()
        cert_schema = web_utils.parser_to_schema(cert_cli.parser)
        custom_broker_field_name = f"{cert_schema['title']}_custom_broker"
        # Only add if not already present
        if custom_broker_field_name not in form_data:
            form_data[custom_broker_field_name] = custom_broker_path
    
    form_dict = FormDict(form_data)
    
    cert_cli = CertificateCLI()
    cert_schema = web_utils.parser_to_schema(cert_cli.parser)
    
    # Create test list
    tl = _write_testlist(selected_tests, form_dict, is_certified)
    
    argv = form_to_argv(form_dict, parser=cert_cli.parser, title=cert_schema['title'])
    # Use absolute path and ensure it's properly formatted (already normalized above)
    schema_path_abs = os.path.abspath(schema_path)
    full_cmd = ["wlt-cert-cli", "--tl", tl, "--validation_schema", schema_path_abs] + argv
    # Add --non_cert_run flag if not certified
    if not is_certified:
        full_cmd.append("--non_cert_run")
    
    if full_cmd:
        p = web_utils.open_in_terminal(full_cmd, preferred=PREFERRED_TERMINAL)
        pid = getattr(p, "pid", None)
    
    # Store run information for popup display
    session['run_completed'] = True
    session['run_terminal'] = PREFERRED_TERMINAL
    session['run_pid'] = str(pid) if pid else None
    session['run_is_certified'] = is_certified
    return redirect(url_for('step', step_num=5))

@app.route("/export_config", methods=['GET'])
def export_config():
    """Export current run configuration to a JSON file."""
    if not session.get('flavor') or not session.get('schema_path'):
        flash("No configuration to export. Please complete at least step 1 and 2.", "error")
        return redirect(url_for('step', step_num=session.get('current_step', 1)))
    
    # Extract custom broker form field values from form_data
    form_data = session.get('form_data', {})
    cert_cli = CertificateCLI()
    cert_schema = web_utils.parser_to_schema(cert_cli.parser)
    custom_broker_fields = {}
    field_prefix = f"{cert_schema['title']}_custom_broker_"
    for field_name in DEFAULT_CUSTOM_BROKER.keys():
        full_field_name = f"{field_prefix}{field_name}"
        if full_field_name in form_data:
            custom_broker_fields[field_name] = form_data[full_field_name]
    
    # Prepare configuration data
    config = {
        'version': '1.0',
        'exported_at': datetime.datetime.now().isoformat(),
        'flavor': session.get('flavor'),
        'schema_path': session.get('schema_path'),
        'selected_modules': session.get('selected_modules', []),
        'selected_tests': session.get('selected_tests', []),
        'form_data': form_data,
        'schema_data': load_schema_data(session.get('schema_path')),  # Load schema data from file for export
        'custom_broker_path': session.get('custom_broker_path'),  # Include custom broker file path for backward compatibility
        'custom_broker_fields': custom_broker_fields  # Include custom broker form field values
    }
    
    # Create filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    flavor_name = session.get('flavor', 'unknown').replace('_', '-')
    filename = f"certificate_run_{flavor_name}_{timestamp}.json"
    filepath = os.path.join(CONFIG_FOLDER, filename)
    
    # Save configuration
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # Send file for download
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/json')

@app.route("/import_config", methods=['POST'])
def import_config():
    """Import a previously saved run configuration."""
    if 'config_file' not in request.files:
        flash("No file selected", "error")
        return redirect(url_for('step', step_num=1))
    
    file = request.files['config_file']
    if not file or not file.filename:
        flash("No file selected", "error")
        return redirect(url_for('step', step_num=1))
    
    if not allowed_file(file.filename):
        flash("Invalid file type. Please upload a JSON file.", "error")
        return redirect(url_for('step', step_num=1))
    
    try:
        # Read and parse JSON
        config_data = json.load(file)
        
        # Validate configuration structure
        if 'version' not in config_data or 'flavor' not in config_data:
            flash("Invalid configuration file format", "error")
            return redirect(url_for('step', step_num=1))
        
        # Restore session data
        session['flavor'] = config_data.get('flavor')
        session['schema_path'] = config_data.get('schema_path')
        session['selected_modules'] = config_data.get('selected_modules', [])
        session['selected_tests'] = config_data.get('selected_tests', [])
        session['form_data'] = config_data.get('form_data', {})
        # Don't restore schema_data to session (load from file when needed to avoid cookie size issues)
        # If schema_data is in config, save it back to the schema_path file if the path exists
        schema_path = config_data.get('schema_path')
        schema_data = config_data.get('schema_data')
        if schema_path and schema_data and os.path.exists(schema_path):
            # Schema file exists, no need to restore schema_data to session
            pass
        elif schema_path and schema_data:
            # Schema file doesn't exist but we have the data - save it
            try:
                with open(schema_path, 'w', encoding='utf-8') as f:
                    json.dump(schema_data, f, indent=2)
            except Exception:
                pass  # If we can't save, user will need to re-upload
        # Handle custom broker configuration
        custom_broker_fields = config_data.get('custom_broker_fields', {})
        if custom_broker_fields:
            # Restore broker form field values to form_data
            cert_cli = CertificateCLI()
            cert_schema = web_utils.parser_to_schema(cert_cli.parser)
            field_prefix = f"{cert_schema['title']}_custom_broker_"
            for field_name, field_value in custom_broker_fields.items():
                full_field_name = f"{field_prefix}{field_name}"
                session['form_data'][full_field_name] = field_value
            # Regenerate broker config file from form fields
            try:
                broker_config_path = _write_custom_broker_config(session['form_data'], cert_schema['title'])
                session['custom_broker_path'] = os.path.normpath(broker_config_path)
            except Exception:
                pass  # If generation fails, user can reconfigure in step 4
        else:
            # Backward compatibility: try to use existing path
            session['custom_broker_path'] = config_data.get('custom_broker_path')
        
        # Validate schema file still exists
        if session['schema_path'] and not os.path.exists(session['schema_path']):
            flash(f"Warning: Schema file not found at {session['schema_path']}. Please re-upload it in step 2.", "warning")
            session['current_step'] = 2
        # Validate custom_broker file still exists if present (or regenerate if we have fields)
        elif session.get('custom_broker_path') and not os.path.exists(session['custom_broker_path']):
            if custom_broker_fields:
                # Regenerate from fields if file doesn't exist
                try:
                    cert_cli = CertificateCLI()
                    cert_schema = web_utils.parser_to_schema(cert_cli.parser)
                    broker_config_path = _write_custom_broker_config(session['form_data'], cert_schema['title'])
                    session['custom_broker_path'] = os.path.normpath(broker_config_path)
                except Exception:
                    flash(f"Warning: Custom broker configuration will be regenerated in step 4.", "warning")
                    if session.get('current_step', 0) < 4:
                        session['current_step'] = 4
            else:
                flash(f"Warning: Custom broker file not found at {session['custom_broker_path']}. Please reconfigure it in step 4.", "warning")
                if session.get('current_step', 0) < 4:
                    session['current_step'] = 4
        else:
            # Determine appropriate step based on what's configured
            if session.get('selected_tests'):
                session['current_step'] = 5
            elif session.get('selected_modules'):
                session['current_step'] = 4
            elif session.get('schema_path'):
                if session.get('flavor') == FLAVOR_GW_ONLY:
                    session['current_step'] = 4
                else:
                    session['current_step'] = 3
            else:
                session['current_step'] = 2
        
        flash("Configuration loaded successfully!", "success")
        return redirect(url_for('step', step_num=session['current_step']))
    
    except json.JSONDecodeError:
        flash("Invalid JSON file", "error")
        return redirect(url_for('step', step_num=1))
    except Exception as e:
        flash(f"Error loading configuration: {str(e)}", "error")
        return redirect(url_for('step', step_num=1))

@app.route("/clear")
def clear_session():
    """Clear session and start fresh."""
    session.clear()
    # Initialize session flags
    session['schema_mandatory_initialized'] = False
    return redirect(url_for('step', step_num=1))

@app.route("/parser")
def parser():
    return web_utils.utils_parser(web_utils.CERT_WEB)

@app.route("/generator")
def generator():
    return web_utils.utils_generator(web_utils.CERT_WEB)

@app.route("/data_structs", methods=['GET', 'POST'])
def data_structs():
    return web_utils.utils_data_structs(web_utils.CERT_WEB)
