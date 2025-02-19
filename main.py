'''Updates Github repo settings to consistent settings.'''
import sys
import os
import requests
import json

# Get personal access token from env. variables
# Personal access token needs full repo rights.
GITHUB_PAT_KEY = 'PERSONAL_ACCESS_TOKEN'
GITHUB_PAT = os.getenv(GITHUB_PAT_KEY)
if GITHUB_PAT is None:
    sys.exit(f"{GITHUB_PAT_KEY} environment variable doesn't exist.")

# Modified requests item
r = requests.Session()
r.headers.update({
    'Authorization': f'Bearer {GITHUB_PAT}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
})

# Configuration values
API_URL = "https://api.github.com/"
USER = "dfar-io"

def main():
    '''Sets all repository settings to consistent settings'''
    repos = get_repos()
    print(f'{"Repo" : <50} {"CICD job?" : <10} {"TFPlan job?" : <10}')
    for repo in repos:
        update_repo(repo)

        has_cicd_job = contains_cicd_workflow_runs(repo)
        has_tfplan_job = contains_tfplan_workflow_runs(repo)
        update_branch_protection(repo, has_cicd_job, has_tfplan_job)

        print(f'{repo : <50} {has_cicd_job : <10} {has_tfplan_job : <10}')

def get_repos():
    '''
    Gets non-readonly repos from Github as a list of strings providing their name.
    https://docs.github.com/en/rest/reference/repos#list-organization-repositories
    '''
    try:
        response = r.get(f'{API_URL}users/{USER}/repos')
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        sys.exit(handle_error('Error when getting repos.', response))

    # Skip archived repos, these cause issues
    writable_repos = [x for x in response.json() if x['archived'] is False]
    repo_names = (e['name'] for e in writable_repos)
    return repo_names

def update_repo(repo):
    '''
    Updates a repo's setting (must not be read-only)
    https://docs.github.com/en/rest/repos/repos#update-a-repository
    '''
    payload = {
        'has_issues': 'false',
        'has_projects': 'false',
        'has_wiki': 'false',
        'allow_squash_merge': 'true',
        'allow_merge_commit': 'false',
        'allow_rebase_merge': 'false',
        'allow_auto_merge': 'false',
        'delete_branch_on_merge': 'true',
        'allow_update_branch': 'true'
    }
    try:
        url = f'{API_URL}repos/{USER}/{repo}'
        response = r.patch(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        sys.exit(handle_error(f'Error when updating \'{repo}\.', response))

def update_branch_protection(repo, has_cicd_job, has_tfplan_job):
    '''
    Updates branch protections
    https://docs.github.com/en/rest/reference/branches#update-branch-protection
    '''

    checks = []
    if has_cicd_job:
        checks.append({ 'context': 'build' })
    if has_tfplan_job:
        checks.append({ 'context': 'tfplan' })
    required_status_checks = {
        'url': f'{API_URL}/repos/{USER}/{repo}/branches/main/protection/required_status_checks',
        'strict': True,
        'checks': checks
    }

    payload = {
        'required_status_checks': required_status_checks,
        'required_pull_request_reviews': {
            'required_approving_review_count': 0
        },
        'enforce_admins': True,
        'restrictions': None
    }

    try:
        response = r.put(f'{API_URL}repos/{USER}/{repo}/branches/main/protection', json=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        sys.exit(
            handle_error(
                f'Error when updating branch protections for \'{repo}\'',
                response))

def branch_exists(branch, repo):
    '''
    Checks if a branch exists in a repo.
    https://docs.github.com/en/rest/reference/repos#list-organization-repositories
    '''
    response = r.get(f'{API_URL}repos/{USER}/{repo}/branches/{branch}')
    return response.status_code == 200

def contains_cicd_workflow_runs(repo):
    '''
    Checks if a repo contains 'cicd.yml' workflow runs
    https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository
    '''
    
    response = r.get(f'{API_URL}repos/{USER}/{repo}/actions/workflows/cicd.yml/runs')
    return response.status_code == 200

def contains_tfplan_workflow_runs(repo):
    '''
    Checks if a repo contains 'tfplan.yml' workflow runs
    https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository
    '''
    
    response = r.get(f'{API_URL}repos/{USER}/{repo}/actions/workflows/tfplan.yml/runs')
    return response.status_code == 200

def handle_error(error_message, res):
    '''Provides improved error reporting'''
    fix = ''
    if (res.status_code == 401):
        fix = 'Change out the Github token being used in both Actions and Codespaces.'

    payload = {
        'error_message': error_message,
        'fix': fix,
        'response_status': res.status_code,
        'response_text': res.text
    }
    return json.dumps(payload, indent=4)

if __name__ == "__main__":
    main()
