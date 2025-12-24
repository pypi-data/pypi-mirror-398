import argparse
import json
import io
import os
import re
import sys
import uuid
import zipfile
from configparser import ConfigParser
from datetime import timedelta, datetime, timezone
from distutils.util import strtobool
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import warnings
from mend_project_cleanup_tool._version import __tool_name__, __version__
from urllib3.exceptions import InsecureRequestWarning

ATTRIBUTION = "attribution"
FILTER_PROJECTS_BY_UPDATE_TIME = "FilterProjectsByUpdateTime"
FILTER_PROJECTS_BY_LAST_CREATED_COPIES = "FilterProjectsByLastCreatedCopies"
FILTER_PROJECTS_BY_LAST_SCAN_DATE = "FilterProjectsByLastScanDate"
AGENT_INFO = {
    'agent': f"ps-{__tool_name__}".replace('_', '-'),
    'agentVersion': __version__
}
HEADERS = {
    'Content-Type': 'application/json',
    'ctxId': uuid.uuid1().__str__()
}
WARNING_MSG = False
IGNORED_ALERTS = "ignored_alerts"
RESOLVED_ALERTS = "resolved_alerts"
REJECTED_BY_POLICY = "alerts_rejected_by_policy"

# API 1.4 Reports (legacy)
REPORTS_API_14 = {
           "bugs": "getProjectBugsReport",
           IGNORED_ALERTS: "getProjectSecurityAlertsByVulnerabilityReport",
           REJECTED_BY_POLICY: "getProjectAlertsByType",
           "in_house_libraries": "getProjectInHouseReport",
           "license_compatibility": "getProjectLicenseCompatibilityReport",
           RESOLVED_ALERTS: "getProjectSecurityAlertsByVulnerabilityReport",
           "source_files": "getProjectSourceFileInventoryReport", 
           "alerts": "getProjectSecurityAlertsByVulnerabilityReport",
           ATTRIBUTION: "getProjectAttributionReport",
           "inventory": "getProjectInventoryReport",
           "request_history": "getProjectRequestHistoryReport",
           "source_file_inventory": "getProjectSourceFileInventoryReport",
           "vulnerability": "getProjectVulnerabilityReport"
           }

# API 3.0 Reports (SCA/Dependencies)
REPORTS_API_30_SCA = {
           "due_diligence": {"endpoint": "dependencies/reports/dueDiligence", "format": "json"},
           "sbom_spdx": {"endpoint": "dependencies/reports/SBOM", "format": "json", "reportType": "spdx_2_3"},
           "sbom_cyclonedx": {"endpoint": "dependencies/reports/SBOM", "format": "json", "reportType": "cycloneDX_1_5"}
           }

# API 3.0 SAST Reports (Code)
REPORTS_API_30_SAST = {
           "sast_findings": {"endpoint": "code/reports/findings", "format": "csv"},
           "sast_suppressions": {"endpoint": "code/reports/suppressions", "format": "csv"}
           }

# API 3.0 Container Reports (Images)
REPORTS_API_30_CONTAINER = {
           "container_due_diligence": {"endpoint": "images/reports/dueDiligence", "format": "json", "reportType": "imgDueDiligence"},
           "container_attribution": {
               "endpoint": "images/reports/attribution",
               "format": "json",
               "reportType": "imgAttribution",
               "payload": {
                   "groupBy": "BY_COMPONENT",
                   "licenseReference": "BLANK",
                   "licenseTextPlacement": "APPENDIX_SECTION",
                   "selectedColumns": [
                       "SUMMARY",
                       "PROJECTS",
                       "PRODUCTS",
                       "LICENSES",
                       "NOTICES",
                       "COPYRIGHTS",
                       "PACKAGE_NAME",
                       "PACKAGE_VERSION"
                   ]
               }
           },
           "container_sbom": {"endpoint": "images/reports/SBOM", "format": "json", "reportType": "imgSpdx_2_3"}
           }
REPORTS = {**REPORTS_API_14}
API_VER = "/api/v2.0"
API_VER_V3 = "/api/v3.0"
API_VER_V14 = "/api/v1.4"
CONFIG = None
JWT_TOKEN = None
TOKEN_EXPIRY = None


def write_dry_run_report(processed_projects):
    """
    Write a CSV file with projects to be deleted for customer review during dry run
    
    Args:
        processed_projects: Dict of {application_name: [filtered_projects]}
    """
    output_dir = CONFIG.output_dir if CONFIG.output_dir else os.getcwd()
    output_dir = output_dir.replace("\\", "/")
    if not output_dir.endswith("/"):
        output_dir = output_dir + "/"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{output_dir}dry_run_projects_to_delete.csv"
    
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            f.write("Application Name,Project Name,Project UUID,Last Updated Date\n")
            
            for application_name, projects in processed_projects.items():
                for project in projects:
                    app_name = f'"{application_name}"' if ',' in application_name else application_name
                    proj_name = f'"{project["name"]}"' if ',' in project['name'] else project['name']
                    proj_uuid = project.get('projectUuid', project.get('token', ''))
                    last_updated = project.get('lastUpdatedDate', '')
                    
                    f.write(f"{app_name},{proj_name},{proj_uuid},{last_updated}\n")
        
        print(f"Dry Run report written to: {filename}")
        return filename
    except Exception as e:
        print(f"Warning: Could not write dry run report: {e}")
        return None


def generate_reports_for_project(project, application_name):
    """
    Generate reports for a single project
    This function is designed to be run in parallel
    
    Args:
        project: Project dict
        application_name: Name of the application (for logging)
    
    Returns:
        Tuple of (project, error) - error is None if successful
    """
    try:
        generate_reports(project)
        return (project, None)
    except Exception as e:
        print(f"{application_name} - There was an issue with the report generation for project: {project['name']}")
        print(e)
        return (project, e)


def delete_project(project, application_name):
    """
    Delete a single project
    This function is designed to be run in parallel
    
    Args:
        project: Project dict
        application_name: Name of the application (for logging)
    
    Returns:
        Tuple of (project, error) - error is None if successful
    """
    try:
        print(f"{application_name} - deleting project {project['name']}")
        delete_scan(project['token'], project)
        print(f"{application_name} - project deleted {project['name']}")
        return (project, None)
    except Exception as e:
        print(f"{application_name} - Error deleting project {project['name']}: {e}")
        return (project, e)


def evaluate_projects():
    """
    Fetch applications/projects and apply operation-mode filtering.
    """
    needs_applications = (
        CONFIG.operation_mode == FILTER_PROJECTS_BY_LAST_CREATED_COPIES or
        CONFIG.included_application_uuids or 
        CONFIG.excluded_application_uuids or
        CONFIG.included_application_labels or
        CONFIG.excluded_application_labels or
        CONFIG.included_application_tag or
        CONFIG.excluded_application_tag or
        CONFIG.included_application_tag_regex_in_value or
        CONFIG.excluded_application_tag_regex_in_value
    )
    
    applications = get_applications() if needs_applications else []
    if len(applications) == 0 and needs_applications:
        print("No applications found based on filtering criteria")
        exit()
    
    all_projects = get_all_projects_once()
    if len(applications) > 0 and CONFIG.operation_mode != FILTER_PROJECTS_BY_LAST_CREATED_COPIES:
        allowed_app_uuids = {application['applicationUuid'] for application in applications}
        all_projects = [p for p in all_projects if p.get('applicationUuid') in allowed_app_uuids]
        print(f"Filtered to {len(all_projects)} project(s) in selected application(s)")

    print(f"Operation Mode: {CONFIG.operation_mode}")
    
    if CONFIG.operation_mode == FILTER_PROJECTS_BY_UPDATE_TIME:
        return process_projects_by_date(all_projects)
    if CONFIG.operation_mode == FILTER_PROJECTS_BY_LAST_SCAN_DATE:
        return process_projects_by_last_scan_date(all_projects)

    processed_projects = {}
    with ThreadPoolExecutor(max_workers=int(CONFIG.project_parallelism_level)) as executor:
        futures = []
        for application in applications:
            futures.append(executor.submit(process_application, application, all_projects))
            
        for future in as_completed(futures):
            processed_projects.update(future.result())
    return processed_projects


def generate_reports_for_projects(processed_projects):
    """
    Generate reports (if enabled) and return projects_to_delete + error tracking.
    """
    errored_projects_by_app = {}
    projects_to_delete = {}
    total_to_delete = sum(len(processed_projects[x]) for x in processed_projects)

    if CONFIG.skip_report_generation:
        projects_to_delete = processed_projects.copy()
        for application_name in processed_projects:
            errored_projects_by_app[application_name] = []
        return projects_to_delete, errored_projects_by_app, total_to_delete

    print(f"Generating reports for {total_to_delete} project(s) in parallel...")
    with ThreadPoolExecutor(max_workers=int(CONFIG.project_parallelism_level)) as executor:
        futures = {}
        
        for application_name, projects in processed_projects.items():
            errored_projects_by_app[application_name] = []
            for project in projects:
                future = executor.submit(generate_reports_for_project, project, application_name)
                futures[future] = (project, application_name)
        
        for future in as_completed(futures):
            project, application_name = futures[future]
            result_project, error = future.result()
            
            if error is not None:
                errored_projects_by_app[application_name].append(result_project)
            else:
                if application_name not in projects_to_delete:
                    projects_to_delete[application_name] = []
                projects_to_delete[application_name].append(result_project)
    total_to_delete = sum(len(projects_to_delete[x]) for x in projects_to_delete)
    print(f"Reports generated for {total_to_delete} project(s)")
    return projects_to_delete, errored_projects_by_app, total_to_delete


def delete_projects(projects_to_delete, processed_projects, errored_projects_by_app):
    """
    Delete projects in parallel (if enabled) and return count deleted.
    """
    if CONFIG.skip_project_deletion:
        return 0

    total_to_delete = sum(len(projects_to_delete[x]) for x in projects_to_delete)
    print(f"Phase 2: Deleting {total_to_delete} project(s) in parallel...")
    
    with ThreadPoolExecutor(max_workers=int(CONFIG.project_parallelism_level)) as executor:
        futures = {}
        
        for application_name, projects in projects_to_delete.items():
            for project in projects:
                future = executor.submit(delete_project, project, application_name)
                futures[future] = (project, application_name)
        
        for future in as_completed(futures):
            project, application_name = futures[future]
            result_project, error = future.result()
            
            if error is not None:
                errored_projects_by_app[application_name].append(result_project)

    for application_name, errored_projects in errored_projects_by_app.items():
        for project in errored_projects:
            if project in processed_projects[application_name]:
                processed_projects[application_name].remove(project)

    total_projects_deleted = sum(len(processed_projects[x]) for x in processed_projects)
    print(f"Deleted {total_projects_deleted} project(s)")
    return total_projects_deleted


def load_config_from_args():
    if len(sys.argv) == 1:
        return parse_config_file("params.config")
    elif not sys.argv[1].startswith('-'):
        return parse_config_file(sys.argv[1])
    else:
        return parse_args()


def run_cleanup():
    if CONFIG.skip_report_generation:
        print("Skip Report Generation Enabled - Reports will not be generated")
    if CONFIG.skip_project_deletion:
        print("Skip Project Deletion Enabled - Projects will not be deleted")

    if CONFIG.dry_run:
        print("Dry Run enabled - no reports or deletions will occur")

    processed_projects = evaluate_projects()
    
    total_projects_to_delete = (sum([len(processed_projects[x]) for x in processed_projects]))   
    if total_projects_to_delete == 0:
        print("No projects to clean up were found")
        exit()
    
    print(f"Found {total_projects_to_delete} project(s) to process")
    
    if not CONFIG.skip_summary:
        for application_name in processed_projects:
            print(f"  {application_name}: {[project['name'] for project in processed_projects[application_name]]}")
    
    if CONFIG.dry_run:
        print(f"Dry Run found {total_projects_to_delete} project(s) to delete")
        write_dry_run_report(processed_projects)
        return

    projects_to_delete, errored_projects_by_app, _ = generate_reports_for_projects(processed_projects)
    delete_projects(projects_to_delete, processed_projects, errored_projects_by_app)


def main():
    global CONFIG
    CONFIG = load_config_from_args()
    setup_config()
    
    print("Authenticating with API 2.0/3.0...")
    authenticate()
    run_cleanup()

def authenticate():
    """Authenticate with API 2.0 and get JWT token"""
    global JWT_TOKEN, TOKEN_EXPIRY
    
    login_data = {
        "email": CONFIG.mend_email,
        "userKey": CONFIG.mend_user_key,
        "orgToken": CONFIG.organization_uuid
    }
    
    try:
        proxy = {"https": CONFIG.proxy, "http": CONFIG.proxy} if CONFIG.proxy else {}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always", InsecureRequestWarning)
            url = f"https://{'api-' if 'saas' in CONFIG.mend_url else ''}{CONFIG.mend_url}{API_VER}/login"
            response = requests.post(
                url=url,
                json=login_data,
                headers={'Content-Type': 'application/json'},
                proxies=proxy
            )
            
            if response.status_code != 200:
                sys.exit(f"Authentication failed: {response.text}")
                
            response_obj = response.json()
            if "retVal" in response_obj and "jwtToken" in response_obj["retVal"]:
                JWT_TOKEN = response_obj["retVal"]["jwtToken"]
                TOKEN_EXPIRY = datetime.utcnow() + timedelta(minutes=29)
                print("Authentication successful")
            else:
                sys.exit(f"Authentication failed: No JWT token in response")
    except Exception as err:
        sys.exit(f'Authentication exception: {err}')

def check_and_refresh_token():
    """Check if token is about to expire and refresh if needed"""
    if TOKEN_EXPIRY and datetime.utcnow() >= TOKEN_EXPIRY:
        print("Token expired, re-authenticating...")
        authenticate()

def _call_api_common(
    endpoint,
    method="GET",
    data=None,
    is_json=True,
    api_version=API_VER,
    api_label="API call",
    headers=None,
    require_auth=True,
    send_json=True,
    raw_text=False
):
    """
    Shared Mend API caller to keep authentication, proxy, and warning handling DRY.
    """
    global WARNING_MSG

    if require_auth:
        check_and_refresh_token()

    api_prefix = 'api-' if api_version != API_VER_V14 else ''
    base_url = f"https://{api_prefix}{CONFIG.mend_url}"
    url = f"{base_url}{api_version}{endpoint}"
    request_headers = headers or {'Content-Type': 'application/json'}
    if require_auth:
        request_headers.setdefault('Content-Type', 'application/json')
        request_headers.setdefault('Authorization', f'Bearer {JWT_TOKEN}')

    try:
        proxy = {"https": CONFIG.proxy, "http": CONFIG.proxy} if CONFIG.proxy else {}
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always", InsecureRequestWarning)

            if method in ["GET", "DELETE"]:
                response = requests.request(method=method, url=url, headers=request_headers, proxies=proxy)
            else:
                payload = data if data else {}
                if send_json:
                    response = requests.request(method=method, url=url, json=payload, headers=request_headers, proxies=proxy)
                else:
                    response = requests.request(method=method, url=url, data=payload, headers=request_headers, proxies=proxy)

            if not WARNING_MSG:
                for warning in warning_list:
                    if issubclass(warning.category, InsecureRequestWarning):
                        index_of_see = str(warning.message).find("See:")
                        print(f"Warning: {str(warning.message)[:index_of_see].strip()}")
                        WARNING_MSG = True

            if response.status_code >= 400:
                print(f"{api_label} failed with status {response.status_code}: {response.text}")
                return None

            if is_json:
                return response.json()
            if raw_text:
                return response.text
            return response.content

    except Exception as err:
        print(f'{api_label} exception: {err}')
        return None


def call_api(endpoint, method="GET", data=None, is_json=True):
    """
    Make API 2.0 REST call with JWT authentication
    """
    return _call_api_common(endpoint, method, data, is_json, api_version=API_VER, api_label="API call")

def call_api_v14(data, header=None, method="POST", report=False):
    """
    Make API 1.4 call for features not available in API 2.0
    (report generation and project tags)
    
    Args:
        data: JSON string with request data
        header: Optional headers
        method: HTTP method (typically POST for API 1.4)
        report: Whether this is a report download (returns bytes)
    
    Returns:
        Response content (JSON string or bytes)
    """
    header = header or HEADERS
    return _call_api_common(
        "",
        method=method,
        data=data,
        is_json=False,
        api_version=API_VER_V14,
        api_label="Legacy API call",
        headers=header,
        require_auth=False,
        send_json=False,
        raw_text=not report
    )

def call_api_v30(endpoint, method="GET", data=None, is_json=True):
    """
    Make API 3.0 REST call with JWT authentication (for cursor-based pagination and labels)
    
    Args:
        endpoint: API endpoint path (e.g., "/orgs/{orgUuid}/projects/summaries")
        method: HTTP method (GET, POST, DELETE, PUT)
        data: Request body data (for POST/PUT)
        is_json: Whether response is JSON (False for binary reports)
    
    Returns:
        Response content (JSON object or bytes)
    """
    return _call_api_common(endpoint, method, data, is_json, api_version=API_VER_V3, api_label="API 3.0 call")

def check_response_error(obj_response):
    if isinstance(obj_response, dict):
        if "errorMessage" in obj_response:
            print(f"There was an issue with the request: {obj_response['errorMessage']}")
            return True
        else:
            return False


def create_output_directory(application_name, project_name):
    application_name = remove_invalid_chars(application_name)
    project_name = remove_invalid_chars(project_name)
    CONFIG.output_dir = CONFIG.output_dir.replace("\\","/")
    if not CONFIG.output_dir.endswith("/"):
        CONFIG.output_dir = CONFIG.output_dir + "/"
    output_dir = CONFIG.output_dir + application_name + "/" + project_name + "/"
    if len(output_dir) > 180:
        output_dir = (output_dir[:180] + "..")
    if not os.path.exists(output_dir):
        print(f"Making directory {output_dir}")
        os.makedirs(output_dir)
    return output_dir


def delete_scan(application_token, project):
    """Delete project using API 2.0 REST DELETE"""
    print(f"{project['applicationName']} - Deleting project: {project['name']}")
    endpoint = f"/projects/{project['token']}"
    response_obj = call_api(endpoint, method="DELETE")
    
    if response_obj:
        check_response_error(response_obj)


def filter_projects_by_config(projects, application_name):
    """
    Filter projects based on configuration parameters
    Note: Operation mode filtering (date vs last N copies) is now handled in main()
    This function applies common filters: excluded UUIDs, name patterns, tags, and labels
    """
    projects_to_return = [project for project in projects if project['projectUuid'] not in CONFIG.excluded_project_uuids]
    if len(projects_to_return) == 0:
        return []

    if CONFIG.excluded_project_name_patterns:
        print(f"{application_name} - Filtering projects with name containing values {CONFIG.project_name_exclude_list}")
        for patt in CONFIG.project_name_exclude_list:
            projects_to_return = [project for project in projects_to_return if patt not in project.get("name", "")]

    if hasattr(CONFIG, 'included_project_labels') and CONFIG.included_project_labels:
        print(f"{application_name} - Filtering projects based on included labels: {CONFIG.included_project_labels}")
        projects_to_return = filter_items_by_included_labels(
            projects_to_return,
            CONFIG.included_project_labels,
            label_getter=lambda project: project.get('labels', []),
            log_excluded=lambda project: print(f"{application_name} - Excluding project '{project['name']}': Does not have required included label")
        )
    
    if hasattr(CONFIG, 'excluded_project_labels') and CONFIG.excluded_project_labels:
        print(f"{application_name} - Filtering projects based on excluded labels: {CONFIG.excluded_project_labels}")
        projects_to_return = filter_items_by_excluded_labels(
            projects_to_return,
            CONFIG.excluded_project_labels,
            label_getter=lambda project: project.get('labels', []),
            log_protected=lambda project, matching: print(f"{application_name} - Project '{project['name']}' has protected labels: {matching} - Will be KEPT")
        )

    if CONFIG.included_project_tag:
        print(f"{application_name} - Filtering projects based on included project tag: {CONFIG.included_project_tag}")
        projects_to_return = filter_items_by_tag(
            projects_to_return,
            getattr(CONFIG, "included_project_tag_pair", None),
            tags_getter=lambda project: project.get('tags', {}),
            include=True,
            regex=False,
            log_match=lambda project: print(f"{project['name']} has matching tag")
        )

    if CONFIG.included_project_tag_regex_in_value:
        print(f"{application_name} - Filtering projects based on included project tag regex pattern: {CONFIG.included_project_tag_regex_in_value}")
        projects_to_return = filter_items_by_tag(
            projects_to_return,
            getattr(CONFIG, "included_project_tag_regex_pair", None),
            tags_getter=lambda project: project.get('tags', {}),
            include=True,
            regex=True,
            log_match=lambda project: print(f"{project['name']} matches tag regex pattern"),
            regex_error_return_items_on_error=False
        )
    
    if getattr(CONFIG, 'excluded_project_tag_pair', None):
        print(f"{application_name} - Filtering projects based on excluded project tag: {CONFIG.excluded_project_tag}")
        projects_to_return = filter_items_by_tag(
            projects_to_return,
            CONFIG.excluded_project_tag_pair,
            tags_getter=lambda project: project.get('tags', {}),
            include=False,
            regex=False,
            log_match=lambda project: print(f"{application_name} - Excluding project '{project['name']}': Has excluded tag {CONFIG.excluded_project_tag_pair[0]}:{CONFIG.excluded_project_tag_pair[1]}")
        )
    
    if getattr(CONFIG, 'excluded_project_tag_regex_pair', None):
        print(f"{application_name} - Filtering projects based on excluded project tag regex: {CONFIG.excluded_project_tag_regex_in_value}")
        projects_to_return = filter_items_by_tag(
            projects_to_return,
            CONFIG.excluded_project_tag_regex_pair,
            tags_getter=lambda project: project.get('tags', {}),
            include=False,
            regex=True,
            log_match=lambda project: print(f"{application_name} - Excluding project '{project['name']}': Matches excluded tag regex"),
            regex_error_return_items_on_error=True
        )

    print(f"{application_name} - {len(projects_to_return)} project(s) to remove after filtering")
    return projects_to_return


def convert_labels_to_strings(labels):
    """
    Helper function to convert labels from API format to list of strings
    Handles both dict and string formats
    
    Args:
        labels: List of labels (can be dicts or strings)
    
    Returns:
        List of label strings in format "namespace:value" or just "value"
    """
    label_strings = []
    for label in labels:
        if isinstance(label, dict):
            namespace = label.get('namespace', '')
            value = label.get('value', '')
            if namespace and value:
                label_strings.append(f"{namespace}:{value}")
            elif value:
                label_strings.append(value)
        elif isinstance(label, str):
            label_strings.append(label)
    return label_strings


def convert_tags_to_dict(tags):
    """
    Helper function to convert tags from API format to dict
    Handles both list and dict formats
    
    Args:
        tags: Tags from API (can be list of dicts or dict)
    
    Returns:
        Dict with tag keys mapping to lists of values
    """
    tags_dict = {}
    if isinstance(tags, list):
        for tag in tags:
            key = tag.get('key', '')
            value = tag.get('value', '')
            if key:
                if key not in tags_dict:
                    tags_dict[key] = []
                tags_dict[key].append(value)
    elif isinstance(tags, dict):
        tags_dict = tags
    return tags_dict


def normalize_label_list(labels):
    """
    Normalize labels into a list of stripped strings.
    Accepts comma-delimited string or list inputs.
    """
    if not labels:
        return []
    if isinstance(labels, str):
        return [label.strip() for label in labels.split(",") if label.strip()]
    return [str(label).strip() for label in labels if str(label).strip()]


def filter_items_by_included_labels(items, included_labels, label_getter, log_excluded=None):
    """
    Keep items that have ANY of the included labels.
    """
    include_list = normalize_label_list(included_labels)
    if not include_list:
        return items

    items_to_keep = []
    for item in items:
        label_strings = convert_labels_to_strings(label_getter(item))
        if any(included_label in label_strings for included_label in include_list):
            items_to_keep.append(item)
        else:
            if log_excluded:
                log_excluded(item)
    return items_to_keep


def filter_items_by_excluded_labels(items, excluded_labels, label_getter, log_protected=None):
    """
    Keep items that do NOT have ANY of the excluded labels.
    """
    exclude_list = normalize_label_list(excluded_labels)
    if not exclude_list:
        return items

    items_to_keep = []
    for item in items:
        label_strings = convert_labels_to_strings(label_getter(item))
        matching = [excluded_label for excluded_label in exclude_list if excluded_label in label_strings]
        if matching:
            if log_protected:
                log_protected(item, matching)
        else:
            items_to_keep.append(item)
    return items_to_keep


def filter_items_by_tag(items, tag_pair, tags_getter, include=True, regex=False, log_match=None, log_no_match=None, regex_error_return_items_on_error=False):
    """
    Generic tag filter for include/exclude and exact/regex matching.
    """
    if not tag_pair:
        return items

    pattern = None
    if regex:
        try:
            pattern = re.compile(tag_pair[1])
        except re.error as e:
            print(f"ERROR: Invalid regex pattern '{tag_pair[1]}': {e}")
            return items if regex_error_return_items_on_error else []

    filtered_items = []
    for item in items:
        tags_dict = convert_tags_to_dict(tags_getter(item))
        matched = False

        for key, values in tags_dict.items():
            key_match = tag_pair[0] in key if regex else key == tag_pair[0]
            if not key_match:
                continue

            values_list = values if isinstance(values, list) else [values]
            if regex:
                if any(pattern.search(str(val)) for val in values_list):
                    matched = True
                    break
            else:
                for val in values_list:
                    if isinstance(val, str):
                        if tag_pair[1] in val:
                            matched = True
                            break
                    elif tag_pair[1] == val:
                        matched = True
                        break

        if include:
            if matched:
                if log_match:
                    log_match(item)
                filtered_items.append(item)
            else:
                if log_no_match:
                    log_no_match(item)
        else:
            if matched:
                if log_match:
                    log_match(item)
            else:
                filtered_items.append(item)

    return filtered_items


def generate_reports(project):
    """
    Generate reports using API 3.0 (where available) or API 1.4 (fallback)
    
    API 3.0 is used for SCA, SAST, and Container reports
    API 1.4 is used for legacy reports not yet available in API 3.0
    """
    application_name = project['applicationName']
    print(f"{application_name} - Generating reports for project: {project['name']}")
    project_uuid = project['projectUuid']
    project_token = project['token']
    reports_to_generate = get_reports_to_generate()
    
    if len(reports_to_generate) > 0:
        base_output_dir = create_output_directory(application_name, project['name'])
        
        has_sca_data = check_project_has_sca_data(project_uuid)
        has_sast_data = check_project_has_sast_data(project_uuid)
        has_container_data = check_project_has_container_data(project_uuid)
        
        for report_name in reports_to_generate.keys():
            data = None
            reportFormat = 'xlsx'
            report_subfolder = None
            
            if has_sca_data:
                if report_name in REPORTS_API_30_SCA:
                    report_config = REPORTS_API_30_SCA[report_name]
                    data = generate_report_v30(project_uuid, report_config, f"{project['name']}_{report_name}")
                    reportFormat = report_config['format']
                    report_subfolder = "SCA"
                elif report_name.lower() == ATTRIBUTION:
                    data = get_attribution_report(project_token)
                    reportFormat = 'html'
                    report_subfolder = "SCA"
                elif report_name.lower() == RESOLVED_ALERTS:
                    data = get_alerts_report(reports_to_generate[report_name], project_token, "resolved")
                    report_subfolder = "SCA"
                elif report_name.lower() == IGNORED_ALERTS:
                    data = get_alerts_report(reports_to_generate[report_name], project_token, "ignored")
                    report_subfolder = "SCA"
                elif report_name.lower() == REJECTED_BY_POLICY:
                    data = get_alerts_by_type(reports_to_generate[report_name], project_token, "REJECTED_BY_POLICY_RESOURCE")
                    reportFormat = "json"
                    report_subfolder = "SCA"
                elif report_name in REPORTS_API_14:
                    data = get_excel_report(reports_to_generate[report_name], project_token)
                    report_subfolder = "SCA"
            elif report_name in REPORTS_API_30_SCA or report_name in REPORTS_API_14 or report_name.lower() in [ATTRIBUTION, RESOLVED_ALERTS, IGNORED_ALERTS, REJECTED_BY_POLICY]:
                print(f"{application_name} - Skipping SCA report '{report_name}': Project has no SCA library data")
                continue
            
            if has_sast_data:
                if report_name in REPORTS_API_30_SAST:
                    report_config = REPORTS_API_30_SAST[report_name]
                    data = generate_report_v30(project_uuid, report_config, f"{project['name']}_{report_name}")
                    reportFormat = report_config['format']
                    report_subfolder = "SAST"
            elif report_name in REPORTS_API_30_SAST:
                print(f"{application_name} - Skipping SAST report '{report_name}': Project has no SAST findings data")
                continue
            
            if has_container_data:
                if report_name in REPORTS_API_30_CONTAINER:
                    report_config = REPORTS_API_30_CONTAINER[report_name]
                    data = generate_report_v30(project_uuid, report_config, f"{project['name']}_{report_name}")
                    reportFormat = report_config['format']
                    report_subfolder = "Container"
            elif report_name in REPORTS_API_30_CONTAINER:
                print(f"{application_name} - Skipping Container report '{report_name}': Project has no Container image packages data")
                continue
            
            if data is None and report_subfolder is None:
                print(f"{application_name} - Unsupported report type: {report_name}")
                continue
            
            if data is None:
                print(f"{application_name} - WARNING: Report '{report_name}' generation failed despite data being present")
                continue
            
            if report_name not in REPORTS_API_30_SCA and report_name not in REPORTS_API_30_SAST and report_name not in REPORTS_API_30_CONTAINER:
                generation_failed = check_response_error(data)
                if generation_failed:
                    raise Exception(f"{application_name} - Failed to generate report: {report_name}")
            else:
                extracted_filename = None
                if isinstance(data, tuple):
                    data, extracted_filename = data
                else:
                    data, extracted_filename = unzip_report_bytes(data)
                if extracted_filename:
                    _, inner_ext = os.path.splitext(extracted_filename)
                    if inner_ext:
                        reportFormat = inner_ext.lstrip('.')
            
            if report_subfolder:
                output_dir = base_output_dir + report_subfolder + os.sep
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                output_dir = base_output_dir
            
            report_file_path = output_dir + report_name + '.' + reportFormat
            with open(report_file_path, "wb") as report_file:
                report_file.write(data)
            print(f"{application_name} - Saved report: {report_file_path}")
    else:
        print(f"{application_name} - No reports to generate")


def get_alerts_report(request_type, project_token, alertType):
    """Generate alerts report using API 1.4"""
    request = json.dumps({
        "requestType": request_type,
        "userKey": CONFIG.mend_user_key,
        "projectToken": project_token,
        "status": alertType,
        "format": "xlsx",
        "agentInfo": AGENT_INFO
    })
    return call_api_v14(data=request, report=True)


def get_alerts_by_type(request_type, project_token, alertType):
    """Generate alerts by type report using API 1.4"""
    request = json.dumps({
        "requestType": request_type,
        "userKey": CONFIG.mend_user_key,
        "projectToken": project_token,
        "alertType": alertType,
        "agentInfo": AGENT_INFO
    })
    return call_api_v14(data=request, report=True)


def get_attribution_report(project_token):
    """Generate attribution report using API 1.4"""
    request = json.dumps({
        "requestType": REPORTS[ATTRIBUTION],
        "userKey": CONFIG.mend_user_key,
        "projectToken": project_token,
        "reportingAggregationMode": "BY_PROJECT",
        "exportFormat": "html",
        "agentInfo": AGENT_INFO
    })
    return call_api_v14(data=request, report=True)


def get_config_file_value(config_val, default):
        if isinstance(config_val, int):
            return config_val if config_val is not None else default
        return config_val if config_val else default


def get_excel_report(request_type, project_token):
    """Generate Excel report using API 1.4"""
    request = json.dumps({
        "requestType": request_type,
        "userKey": CONFIG.mend_user_key,
        "projectToken": project_token,
        "format": "xlsx",
        "agentInfo": AGENT_INFO
    })
    return call_api_v14(data=request, report=True)


def check_project_has_sca_data(project_uuid):
    """
    Check if project has SCA (Dependencies) data by querying libraries endpoint
    Returns True if project has libraries, False otherwise
    """
    endpoint = f"/projects/{project_uuid}/dependencies/libraries?limit=1"
    response_obj = call_api_v30(endpoint, method="GET", data={})
    
    if not response_obj or check_response_error(response_obj):
        return False
    
    if "response" in response_obj:
        libraries = response_obj["response"]
        return len(libraries) > 0
    
    return False


def check_project_has_sast_data(project_uuid):
    """
    Check if project has SAST (Code) data by querying findings endpoint
    Returns True if project has findings, False otherwise
    """
    endpoint = f"/projects/{project_uuid}/code/findings?limit=1"
    response_obj = call_api_v30(endpoint, method="GET", data={})
    
    if not response_obj or check_response_error(response_obj):
        return False
    
    if "response" in response_obj:
        findings = response_obj["response"]
        return len(findings) > 0
    
    return False


def check_project_has_container_data(project_uuid):
    """
    Check if project has Container (Images) data by querying packages endpoint
    Returns True if project has packages, False otherwise
    """
    endpoint = f"/projects/{project_uuid}/images/packages?limit=1"
    response_obj = call_api_v30(endpoint, method="GET", data={})
    
    if not response_obj or check_response_error(response_obj):
        return False
    
    if "response" in response_obj:
        packages = response_obj["response"]
        return len(packages) > 0
    
    return False


def generate_report_v30(project_uuid, report_config, report_name):
    """
    Generate report using API 3.0 (async workflow)
    
    Args:
        project_uuid: UUID of the project
        report_config: Dict with 'endpoint', 'format', and optional 'reportType'
        report_name: Name for the report
    
    Returns:
        Tuple of (report data bytes, inner filename or None) or None if failed
    """
    import time
    
    endpoint = f"/projects/{project_uuid}/{report_config['endpoint']}"
    report_format = report_config['format']
    
    request_body = {
        "name": report_name,
        "format": report_format,
        "sendEmailNotification": False
    }
    
    if 'reportType' in report_config:
        request_body['reportType'] = report_config['reportType']
    if 'payload' in report_config:
        request_body.update(report_config['payload'])
    
    response_obj = call_api_v30(endpoint, method="POST", data=request_body)
    
    if not response_obj:
        print(f"ERROR: No response from API when initiating report")
        return None
    
    if check_response_error(response_obj):
        print(f"ERROR: API returned error when initiating report")
        return None
    
    if "response" not in response_obj or "uuid" not in response_obj["response"]:
        print(f"ERROR: Failed to get report UUID from response")
        return None
    
    report_uuid = response_obj["response"]["uuid"]
    
    max_attempts = 60
    for attempt in range(max_attempts):
        time.sleep(5)
        
        status_endpoint = f"/orgs/{CONFIG.organization_uuid}/reports/{report_uuid}"
        status_response = call_api_v30(status_endpoint, method="GET", data={})
        
        if not status_response or check_response_error(status_response):
            continue
        
        if "response" in status_response:
            status_data = status_response["response"]
            status = status_data.get("status", "").upper()
            
            if status == "SUCCESS":
                download_endpoint = f"/orgs/{CONFIG.organization_uuid}/reports/download/{report_uuid}"
                report_data = call_api_v30(download_endpoint, method="GET", data={}, is_json=False)
                
                if report_data:
                    return unzip_report_bytes(report_data)
                else:
                    print(f"ERROR: Failed to download report")
                    return None
            elif status in ["FAILED", "CANCELLED"]:
                error_msg = status_data.get("message", "Unknown error")
                print(f"ERROR: Report generation failed: {error_msg}")
                return None
    
    print(f"ERROR: Report generation timed out after {max_attempts * 5} seconds")
    return None


def unzip_report_bytes(report_bytes):
    """
    Unzip a report payload and return the first file's bytes and filename.
    If not a zip or unzip fails, return the original bytes and None.
    """
    if not isinstance(report_bytes, (bytes, bytearray)):
        return report_bytes, None
    if not report_bytes.startswith(b"PK\x03\x04"):
        return report_bytes, None
    try:
        with zipfile.ZipFile(io.BytesIO(report_bytes)) as zf:
            names = zf.namelist()
            if not names:
                print("WARNING: Zip report contained no files")
                return report_bytes, None
            first_name = names[0]
            return zf.read(first_name), first_name
    except Exception as exc:
        print(f"WARNING: Could not unzip report payload: {exc}")
        return report_bytes, None


def get_reports_to_generate():
    """
    Get reports to generate from config, supporting both API 1.4 and API 3.0 reports
    """
    all_reports = {
        **REPORTS_API_14,
        **REPORTS_API_30_SCA,
        **REPORTS_API_30_SAST,
        **REPORTS_API_30_CONTAINER
    }
    
    if len(CONFIG.report_types) == 0:
        return all_reports
    else:
        reportKeys = CONFIG.report_types.replace(" ", "").split(',')
        report_dictionary = {}
        
        for key in reportKeys:
            if key in all_reports:
                report_dictionary[key] = all_reports[key]
        
        if len(report_dictionary) != len(reportKeys):
            unmatched_keys = [k for k in reportKeys if k not in report_dictionary.keys()]
            for unmatched_key in unmatched_keys:
                print(f"Could not generate report for {unmatched_key}. Unsupported report, please reference the README for supported reports")
        
        return report_dictionary


def get_applications():
    """
    Get all products/applications using API 3.0 with cursor pagination and UUIDs
    
    Supports filtering by:
    - Application UUIDs (included/excluded)
    - Application labels (included/excluded)
    - Application tags (included/excluded, with exact match or regex pattern)
    """
    all_applications = []
    cursor = None
    limit = 10000
    
    print(f"Fetching applications")
    
    while True:
        endpoint = f"/orgs/{CONFIG.organization_uuid}/applications/summaries?limit={limit}"
        if cursor:
            endpoint += f"&cursor={cursor}"
        
        response_obj = call_api_v30(endpoint, method="POST", data={})
        
        if not response_obj or check_response_error(response_obj):
            break
        
        if "response" in response_obj:
            applications = response_obj["response"]
            if not applications:
                break
            all_applications.extend(applications)
            
            if "additionalData" in response_obj and "cursor" in response_obj["additionalData"]:
                cursor = response_obj["additionalData"]["cursor"]
            else:
                break
        else:
            break
    
    print(f"Retrieved {len(all_applications)} applications")
    
    applications_converted = []
    for app in all_applications:
        app_converted = {
            'applicationName': app.get('name', ''),
            'applicationUuid': app.get('uuid', ''),
            'applicationToken': app.get('uuid', ''),
            'labels': app.get('labels', []),
            'tags': app.get('tags', [])
        }
        applications_converted.append(app_converted)
    
    if CONFIG.included_application_uuids or CONFIG.excluded_application_uuids:
        print(f"Filtering applications by included/excluded UUIDs...")
        if len(CONFIG.included_application_uuids) == 0:
            applications_converted = [app for app in applications_converted if app['applicationUuid'] not in CONFIG.excluded_application_uuids]
        else:
            applications_converted = [app for app in applications_converted if app['applicationUuid'] in CONFIG.included_application_uuids and app['applicationUuid'] not in CONFIG.excluded_application_uuids]
        print(f"Filtered to {len(applications_converted)} application(s) after UUID filtering")
    
    if hasattr(CONFIG, 'included_application_labels') and CONFIG.included_application_labels:
        print(f"Filtering applications by included labels: {CONFIG.included_application_labels}")
        applications_converted = filter_items_by_included_labels(
            applications_converted,
            CONFIG.included_application_labels,
            label_getter=lambda app: app.get('labels', []),
            log_excluded=lambda app: print(f"Excluding application '{app['applicationName']}': Does not have required included label")
        )
    
    if hasattr(CONFIG, 'excluded_application_labels') and CONFIG.excluded_application_labels:
        print(f"Filtering applications by excluded labels: {CONFIG.excluded_application_labels}")
        applications_converted = filter_items_by_excluded_labels(
            applications_converted,
            CONFIG.excluded_application_labels,
            label_getter=lambda app: app.get('labels', []),
            log_protected=lambda app, _: print(f"Excluding application '{app['applicationName']}': Has excluded label")
        )
    
    if hasattr(CONFIG, 'included_application_tag') and CONFIG.included_application_tag:
        print(f"Filtering applications by included tag: {CONFIG.included_application_tag}")
        applications_converted = filter_items_by_tag(
            applications_converted,
            getattr(CONFIG, "included_application_tag_pair", None),
            tags_getter=lambda app: app.get('tags', {}),
            include=True,
            regex=False,
            log_match=lambda app: print(f"Application '{app['applicationName']}' has matching tag"),
            log_no_match=lambda app: print(f"Excluding application '{app['applicationName']}': Does not have required tag {CONFIG.included_application_tag_pair[0]}:{CONFIG.included_application_tag_pair[1]}")
        )
    
    if hasattr(CONFIG, 'included_application_tag_regex_in_value') and CONFIG.included_application_tag_regex_in_value:
        print(f"Filtering applications by included tag regex pattern: {CONFIG.included_application_tag_regex_in_value}")
        applications_converted = filter_items_by_tag(
            applications_converted,
            getattr(CONFIG, "included_application_tag_regex_pair", None),
            tags_getter=lambda app: app.get('tags', {}),
            include=True,
            regex=True,
            log_match=lambda app: print(f"Application '{app['applicationName']}' matches tag regex pattern"),
            log_no_match=lambda app: print(f"Excluding application '{app['applicationName']}': Does not match required tag regex"),
            regex_error_return_items_on_error=False
        )
    
    if hasattr(CONFIG, 'excluded_application_tag') and CONFIG.excluded_application_tag:
        print(f"Filtering applications by excluded tag: {CONFIG.excluded_application_tag}")
        applications_converted = filter_items_by_tag(
            applications_converted,
            getattr(CONFIG, "excluded_application_tag_pair", None),
            tags_getter=lambda app: app.get('tags', {}),
            include=False,
            regex=False,
            log_match=lambda app: print(f"Excluding application '{app['applicationName']}': Has excluded tag {CONFIG.excluded_application_tag_pair[0]}:{CONFIG.excluded_application_tag_pair[1]}")
        )
    
    if hasattr(CONFIG, 'excluded_application_tag_regex_in_value') and CONFIG.excluded_application_tag_regex_in_value:
        print(f"Filtering applications by excluded tag regex pattern: {CONFIG.excluded_application_tag_regex_in_value}")
        applications_converted = filter_items_by_tag(
            applications_converted,
            getattr(CONFIG, "excluded_application_tag_regex_pair", None),
            tags_getter=lambda app: app.get('tags', {}),
            include=False,
            regex=True,
            log_match=lambda app: print(f"Excluding application '{app['applicationName']}': Matches excluded tag regex"),
            regex_error_return_items_on_error=True
        )
    
    print(f"Processing {len(applications_converted)} application(s) after all filtering")
    return applications_converted


def get_all_projects_once():
    """
    Fetch ALL projects org-wide using API 3.0 with cursor pagination (called once)
    API 3.0 provides efficient cursor-based pagination and includes labels in the response
    Returns converted projects that can be filtered locally by applicationUuid
    """
    all_projects = []
    cursor = None
    limit = 10000
    
    print("Fetching all projects from organization...")
    
    while True:
        endpoint = f"/orgs/{CONFIG.organization_uuid}/projects/summaries?limit={limit}&categories=LAST_SCAN"
        if cursor:
            endpoint += f"&cursor={cursor}"
        
        response_obj = call_api_v30(endpoint, method="POST", data={})
        
        if not response_obj or check_response_error(response_obj):
            break
        
        if "response" in response_obj:
            projects = response_obj["response"]
            if not projects:
                break
            all_projects.extend(projects)
            
            if "additionalData" in response_obj and "cursor" in response_obj["additionalData"]:
                cursor = response_obj["additionalData"]["cursor"]
            else:
                break
        else:
            break
    
    print(f"Retrieved {len(all_projects)} total project(s) from organization")
    
    projects_converted = []
    for project in all_projects:
        project_uuid = project.get('uuid', '')
        
        last_scan_time_ms = project.get('statistics', {}).get('LAST_SCAN', {}).get('lastScanTime')
        
        try:
            dt = datetime.fromtimestamp(last_scan_time_ms / 1000, tz=timezone.utc)
            formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S %z')
        except (TypeError, ValueError, OSError):
            formatted_date = "1970-01-01 00:00:00 +0000"
        
        project_converted = {
            'name': project.get('name', ''),
            'projectUuid': project_uuid,
            'token': project_uuid,
            'applicationUuid': project.get('applicationUuid', ''),
            'applicationName': project.get('path', 'Unknown'),
            'lastUpdatedDate': formatted_date,
            'labels': project.get('labels', []),
            'tags': project.get('tags', {})
        }
        projects_converted.append(project_converted)
    
    return projects_converted


def filter_projects_by_application(all_projects, application_uuid, application_name="Unknown"):
    """
    Filter cached projects by applicationUuid (local filtering, no API call)
    
    Args:
        all_projects: List of all projects from get_all_projects_once()
        application_uuid: UUID of the application to filter by
        application_name: Name of the application (for logging)
    
    Returns:
        List of projects that belong to the specified application
    """
    filtered_projects = [
        project for project in all_projects 
        if project.get('applicationUuid') == application_uuid
    ]
    
    print(f"{len(filtered_projects)} project(s) found for application '{application_name}'")
    return filtered_projects


def parse_args():
    parser = argparse.ArgumentParser(description="Mend SCA Clean up tool - API 3.0 Edition")
    parser.add_argument('-em', '--email', help="Mend user email", dest='mend_email', required=True)
    parser.add_argument('-u', '--userKey', help="Mend UserKey", dest='mend_user_key', required=True)
    parser.add_argument('-k', '--organizationUuid', help="Mend Organization UUID", dest='organization_uuid', required=True)
    parser.add_argument('-a', '--mendURL', help="Mend URL", dest='mend_url', default="saas.mend.io")
    parser.add_argument('-m', '--operationMode', help="Clean up operation method", dest='operation_mode', default=FILTER_PROJECTS_BY_UPDATE_TIME,
                                choices=[FILTER_PROJECTS_BY_UPDATE_TIME, FILTER_PROJECTS_BY_LAST_CREATED_COPIES, FILTER_PROJECTS_BY_LAST_SCAN_DATE])
    parser.add_argument('-r', '--daysToKeep', help="Number of days to keep", dest='days_to_keep', type=int, default=21)
    parser.add_argument('-d', '--lastScanDate', help="Last scan date in MMDDYYYY format (used with FilterProjectsByLastScanDate mode)", dest='last_scan_date')
    parser.add_argument('-i', '--includedApplicationUuids', help="Included Application UUIDs (comma separated)", dest='included_application_uuids')
    parser.add_argument('-e', '--excludedApplicationUuids', help="Excluded Application UUIDs (comma separated)", dest='excluded_application_uuids')
    parser.add_argument('-x', '--excludedProjectUuids', help="Excluded Project UUIDs (comma separated)", dest='excluded_project_uuids')
    parser.add_argument('-n', '--excludedProjectNamePatterns', help="Excluded project name patterns (comma separated)", dest='excluded_project_name_patterns')
    parser.add_argument('-l', '--labels', help="Excluded Project labels (comma separated). Projects WITHOUT these labels will be DELETED", dest='excluded_project_labels')
    parser.add_argument('--includedProjectLabels', help="Included Project labels (comma separated)", dest='included_project_labels')
    parser.add_argument('-g', '--includedProjectTag', help="Include projects with specific tag (key:value)", dest='included_project_tag')
    parser.add_argument('-v', '--includedProjectTagRegexInValue', help="Include projects with tag regex pattern match (key:regex_pattern)", dest='included_project_tag_regex_in_value')
    parser.add_argument('--excludedProjectTag', help="Exclude projects with specific tag (key:value)", dest='excluded_project_tag')
    parser.add_argument('--excludedProjectTagRegexInValue', help="Exclude projects with tag regex pattern match (key:regex_pattern)", dest='excluded_project_tag_regex_in_value')
    parser.add_argument('--includedApplicationLabels', help="Included Application labels (comma separated)", dest='included_application_labels')
    parser.add_argument('--excludedApplicationLabels', help="Excluded Application labels (comma separated)", dest='excluded_application_labels')
    parser.add_argument('--includedApplicationTag', help="Include applications with specific tag (key:value)", dest='included_application_tag')
    parser.add_argument('--includedApplicationTagRegexInValue', help="Include applications with tag regex pattern match (key:regex_pattern)", dest='included_application_tag_regex_in_value')
    parser.add_argument('--excludedApplicationTag', help="Exclude applications with specific tag (key:value)", dest='excluded_application_tag')
    parser.add_argument('--excludedApplicationTagRegexInValue', help="Exclude applications with tag regex pattern match (key:regex_pattern)", dest='excluded_application_tag_regex_in_value')
    parser.add_argument('-t', '--reportTypes', help="Report types to generate (comma separated)", dest='report_types')
    parser.add_argument('-s', '--skipReportGeneration', help="Skip report generation", dest='skip_report_generation', type=strtobool, default=False)
    parser.add_argument('-y', '--dryRun', help="Dry run mode - preview changes without executing", dest='dry_run', type=strtobool, default=False)
    parser.add_argument('-j', '--skipProjectDeletion', help="Skip project deletion", dest='skip_project_deletion', type=strtobool, default=False)
    parser.add_argument('-ss', '--skipSummary', help="Skip summary of deleted projects", dest='skip_summary', type=strtobool, default=False)
    parser.add_argument('-o', '--outputDir', help="Output directory", dest='output_dir', default=os.getcwd() + "/Mend/Reports/")
    parser.add_argument('-p', '--projectParallelismLevel', help="Maximum number of parallel threads", dest='project_parallelism_level', type=int, default=5)
    parser.add_argument('-pr', '--proxy', help="Proxy URL", dest='proxy', default="")
    return parser.parse_args()


def parse_config_file(filepath):
    if os.path.exists(filepath):
        config = ConfigParser()
        config.optionxform = str
        config.read(filepath)
        return argparse.Namespace(
                    mend_user_key=get_config_file_value(config['DEFAULT'].get("MendUserKey"), os.environ.get("MEND_USER_KEY")),
                    organization_uuid=get_config_file_value(config['DEFAULT'].get("OrganizationUuid"), os.environ.get("ORGANIZATION_UUID")),
                    mend_url=get_config_file_value(config['DEFAULT'].get("MendUrl"), os.environ.get("MEND_URL")),
                    mend_email=get_config_file_value(config['DEFAULT'].get("MendEmail"), os.environ.get("MEND_EMAIL")),
                    report_types=get_config_file_value(config['DEFAULT'].get('ReportTypes'), os.environ.get("REPORT_TYPES")),
                    operation_mode=get_config_file_value(config['DEFAULT'].get("OperationMode"), FILTER_PROJECTS_BY_UPDATE_TIME),
                    output_dir=get_config_file_value(config['DEFAULT'].get('OutputDir'), os.getcwd() + "/Mend/Reports/"),
                    excluded_application_uuids=get_config_file_value(config['DEFAULT'].get("ExcludedApplicationUuids", []), os.environ.get("EXCLUDED_APPLICATION_UUIDS")),
                    included_application_uuids=get_config_file_value(config['DEFAULT'].get("IncludedApplicationUuids", []), os.environ.get("INCLUDED_APPLICATION_UUIDS")),
                    excluded_project_uuids=get_config_file_value(config['DEFAULT'].get("ExcludedProjectUuids", []), os.environ.get("EXCLUDED_PROJECT_UUIDS")),
                    excluded_project_name_patterns=get_config_file_value(config['DEFAULT'].get("ExcludedProjectNamePatterns", None), os.environ.get("EXCLUDED_PROJECT_NAME_PATTERNS")),
                    excluded_project_labels=get_config_file_value(config['DEFAULT'].get("ExcludedProjectLabels", None), os.environ.get("EXCLUDED_PROJECT_LABELS")),
                    included_project_labels=get_config_file_value(config['DEFAULT'].get("IncludedProjectLabels", None), os.environ.get("INCLUDED_PROJECT_LABELS")),
                    included_project_tag=get_config_file_value(config['DEFAULT'].get("IncludedProjectTag", None), os.environ.get("INCLUDED_PROJECT_TAG")),
                    included_project_tag_regex_in_value=get_config_file_value(config['DEFAULT'].get("IncludedProjectTagRegexInValue", None), os.environ.get("INCLUDED_PROJECT_TAG_REGEX_IN_VALUE")),
                    excluded_project_tag=get_config_file_value(config['DEFAULT'].get("ExcludedProjectTag", None), os.environ.get("EXCLUDED_PROJECT_TAG")),
                    excluded_project_tag_regex_in_value=get_config_file_value(config['DEFAULT'].get("ExcludedprojectTagRegexInValue", None), os.environ.get("EXCLUDED_PROJECT_TAG_REGEX_IN_VALUE")),
                    included_application_labels=get_config_file_value(config['DEFAULT'].get("IncludedApplicationLabels", None), os.environ.get("INCLUDED_APPLICATION_LABELS")),
                    excluded_application_labels=get_config_file_value(config['DEFAULT'].get("ExcludedApplicationLabels", None), os.environ.get("EXCLUDED_APPLICATION_LABELS")),
                    included_application_tag=get_config_file_value(config['DEFAULT'].get("IncludedApplicationTag", None), os.environ.get("INCLUDED_APPLICATION_TAG")),
                    included_application_tag_regex_in_value=get_config_file_value(config['DEFAULT'].get("IncludedApplicationTagRegexInValue", None), os.environ.get("INCLUDED_APPLICATION_TAG_REGEX_IN_VALUE")),
                    excluded_application_tag=get_config_file_value(config['DEFAULT'].get("ExcludedApplicationTag", None), os.environ.get("EXCLUDED_APPLICATION_TAG")),
                    excluded_application_tag_regex_in_value=get_config_file_value(config['DEFAULT'].get("ExcludedApplicationTagRegexInValue", None), os.environ.get("EXCLUDED_APPLICATION_TAG_REGEX_IN_VALUE")),
                    days_to_keep=get_config_file_value(config['DEFAULT'].getint("DaysToKeep", 21), os.environ.get("DAYS_TO_KEEP")),
                    last_scan_date=get_config_file_value(config['DEFAULT'].get("LastScanDate", None), os.environ.get("LAST_SCAN_DATE")),
                    project_parallelism_level=config['DEFAULT'].get('ProjectParallelismLevel', 5),
                    dry_run=config['DEFAULT'].getboolean("DryRun", False),
                    skip_report_generation=config['DEFAULT'].getboolean("SkipReportGeneration", False),
                    skip_project_deletion=config['DEFAULT'].getboolean("SkipProjectDeletion", False),
                    proxy=get_config_file_value(config['DEFAULT'].get("ProxyUrl"),""),
                    skip_summary=get_config_file_value(config['DEFAULT'].getboolean("SkipSummary"),False)
                )
    else:
        print(f"No configuration file found at: {filepath}")
        exit()

def process_projects_by_date(all_projects):
    """
    Filter projects for date-based filtering (FILTER_PROJECTS_BY_UPDATE_TIME)
    This is more efficient than grouping by application since we're filtering by date across all projects
    
    Args:
        all_projects: List of all projects (already filtered by application if needed)
    
    Returns:
        Dict of {application_name: [filtered_projects]} grouped by application for summary
    """
    print(f"Filtering {len(all_projects)} project(s) by date and other criteria...")
    
    archive_date = (datetime.utcnow() - timedelta(days=CONFIG.days_to_keep))
    print(f"Filtering projects older than: {archive_date}")
    projects_by_date = [project for project in all_projects if archive_date.timestamp() > datetime.strptime(project['lastUpdatedDate'],'%Y-%m-%d %H:%M:%S %z').timestamp()]
    filtered_projects = filter_projects_by_config(projects_by_date, "All Applications")
    
    return group_projects_by_application(filtered_projects)


def process_projects_by_last_scan_date(all_projects):
    """
    Filter projects by last scan date (FILTER_PROJECTS_BY_LAST_SCAN_DATE)
    Compares project last scan time against a specific date provided by the user
    
    Args:
        all_projects: List of all projects (already filtered by application if needed)
    
    Returns:
        Dict of {application_name: [filtered_projects]} grouped by application for summary
    """
    print(f"Filtering {len(all_projects)} project(s) by last scan date and other criteria...")
    
    target_date = CONFIG.parsed_last_scan_date
    print(f"Filtering projects with last scan before: {target_date.strftime('%Y-%m-%d')}")
    
    projects_by_scan_date = []
    for project in all_projects:
        try:
            project_scan_date = datetime.strptime(project['lastUpdatedDate'], '%Y-%m-%d %H:%M:%S %z')
            if project_scan_date < target_date:
                projects_by_scan_date.append(project)
        except (ValueError, KeyError):
            print(f"Warning: Could not parse date for project {project.get('name', 'Unknown')}")
            continue
    
    print(f"Found {len(projects_by_scan_date)} project(s) with last scan before {target_date.strftime('%Y-%m-%d')}")
    
    filtered_projects = filter_projects_by_config(projects_by_scan_date, "All Applications")
    
    return group_projects_by_application(filtered_projects)


def process_application(application, all_projects):
    """
    Filter projects for a single application for FILTER_PROJECTS_BY_LAST_CREATED_COPIES mode
    
    Args:
        application: Application dict with applicationName, applicationUuid, applicationToken
        all_projects: Cached list of all projects from get_all_projects_once()
    
    Returns:
        Dict of {application_name: [filtered_projects]}
    """
    application_processed_projects = {}
    application_name = application['applicationName']
    print(f"*** Processing application '{application_name}' ***")
    
    projects = filter_projects_by_application(all_projects, application['applicationUuid'], application_name)
    
    filtered_projects = filter_projects_by_config(projects, application_name)
    
    print(f"{application_name} - Filtering projects besides most recent: {CONFIG.days_to_keep}")
    if len(filtered_projects) > CONFIG.days_to_keep:
        index = len(filtered_projects) - CONFIG.days_to_keep
        print(f"{application_name} - Total Projects: {len(filtered_projects)}. Removing oldest {index}")
        filtered_projects = sorted(filtered_projects, key=lambda d: d['lastUpdatedDate'])
        filtered_projects = filtered_projects[:index]
    else:
        print(f"{application_name} - Total Projects: {len(filtered_projects)}. Nothing to filter")
        filtered_projects = []
    
    if len(filtered_projects) == 0:
        print(f"{application_name} - No projects to remove")
    
    application_processed_projects[application_name] = filtered_projects
    return application_processed_projects


def remove_invalid_chars(string_to_clean):
    return re.sub('[:*<>/"?|]', '-', string_to_clean).replace("\\", "-")


def group_projects_by_application(projects):
    """
    Group projects by application for summary output.
    """
    processed_by_app = {}
    for project in projects:
        application_name = project.get('applicationName', 'Unknown')
        processed_by_app.setdefault(application_name, []).append(project)
    return processed_by_app


def parse_and_set_tag_pair(tag_value, friendly_name, attribute_name):
    """
    Parse a tag string in the format key:value and assign it to CONFIG.<attribute_name>.
    """
    if not tag_value:
        return
    tag_pair = tuple(tag_value.replace(" ", "").split(":"))
    if len(tag_pair) != 2:
        print(f"Unable to parse {friendly_name}: {tag_value}")
        sys.exit(f"Expected format of {friendly_name}: <name:value>")
    setattr(CONFIG, attribute_name, tag_pair)


def setup_config():
    if not CONFIG.mend_user_key:
        sys.exit(f"A Mend user key was not provided")
    if not CONFIG.organization_uuid:
        sys.exit(f"A Mend Organization UUID was not provided")
    if not CONFIG.mend_email:
        sys.exit(f"A Mend email was not provided (required for API 2.0 authentication)")

    if CONFIG.mend_url:
        CONFIG.mend_url = re.sub("(https?)://", "", CONFIG.mend_url.lower())
        CONFIG.mend_url = CONFIG.mend_url.replace("api-", "")
        if '/' in CONFIG.mend_url:
            apiIndex = CONFIG.mend_url.find('/')
        else:
            apiIndex = len(CONFIG.mend_url)
        CONFIG.mend_url = CONFIG.mend_url[:apiIndex]
    else:
        sys.exit(f"A Mend URL was not provided") 

    parse_and_set_tag_pair(getattr(CONFIG, 'included_project_tag', None), "project tag", "included_project_tag_pair")
    parse_and_set_tag_pair(getattr(CONFIG, 'included_project_tag_regex_in_value', None), "project tag", "included_project_tag_regex_pair")
    parse_and_set_tag_pair(getattr(CONFIG, 'excluded_project_tag', None), "project tag", "excluded_project_tag_pair")
    parse_and_set_tag_pair(getattr(CONFIG, 'excluded_project_tag_regex_in_value', None), "project tag", "excluded_project_tag_regex_pair")
    parse_and_set_tag_pair(getattr(CONFIG, 'included_application_tag', None), "application tag", "included_application_tag_pair")
    parse_and_set_tag_pair(getattr(CONFIG, 'included_application_tag_regex_in_value', None), "application tag", "included_application_tag_regex_pair")
    parse_and_set_tag_pair(getattr(CONFIG, 'excluded_application_tag', None), "application tag", "excluded_application_tag_pair")
    parse_and_set_tag_pair(getattr(CONFIG, 'excluded_application_tag_regex_in_value', None), "application tag", "excluded_application_tag_regex_pair")

    if CONFIG.operation_mode == FILTER_PROJECTS_BY_LAST_SCAN_DATE:
        if not hasattr(CONFIG, 'last_scan_date') or not CONFIG.last_scan_date:
            sys.exit("Last scan date is required when using FilterProjectsByLastScanDate mode. Please provide a date in MMDDYYYY format.")
        
        CONFIG.last_scan_date = str(CONFIG.last_scan_date).strip()
        
        try:
            CONFIG.parsed_last_scan_date = datetime.strptime(CONFIG.last_scan_date, '%m%d%Y').replace(tzinfo=timezone.utc)
            print(f"Filtering projects with last scan before: {CONFIG.parsed_last_scan_date.strftime('%Y-%m-%d')}")
        except ValueError as e:
            sys.exit(f"Invalid date format: '{CONFIG.last_scan_date}' (length: {len(CONFIG.last_scan_date)}). Expected format: MMDDYYYY (e.g., 01152025 for January 15, 2025). Error: {e}")
    else:
        if CONFIG.days_to_keep is None:
            print("Days to keep was not provided, defaulting to 21")
            CONFIG.days_to_keep = 21
    
    CONFIG.included_application_uuids = CONFIG.included_application_uuids.replace(" ", "").split(",") if CONFIG.included_application_uuids else []
    CONFIG.excluded_application_uuids = CONFIG.excluded_application_uuids.replace(" ", "").split(",") if CONFIG.excluded_application_uuids else []
    CONFIG.excluded_project_uuids = CONFIG.excluded_project_uuids.replace(" ", "").split(",") if CONFIG.excluded_project_uuids else []
    CONFIG.excluded_project_name_patterns = CONFIG.excluded_project_name_patterns.split(",") if CONFIG.excluded_project_name_patterns else []
    CONFIG.report_types = CONFIG.report_types if CONFIG.report_types else []
    
    if CONFIG.excluded_project_labels:
        CONFIG.excluded_project_labels = CONFIG.excluded_project_labels.replace(" ", "").split(",") if CONFIG.excluded_project_labels else []
    else:
        CONFIG.excluded_project_labels = []

    if CONFIG.excluded_project_name_patterns:
        CONFIG.project_name_exclude_list = CONFIG.excluded_project_name_patterns

    if CONFIG.proxy:
        if "http://" not in CONFIG.proxy and "https://" not in CONFIG.proxy:
            CONFIG.proxy = f'http://{CONFIG.proxy}'
        if CONFIG.proxy.count(":") < 2:
            print("The proxy URL was provided but not defined correctly. The right format is <proxy_ip>:<proxy_port>")
            exit()


if __name__ == "__main__":
    main()
