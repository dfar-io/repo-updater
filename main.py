'''Updates Github repo settings to consistent settings.'''
import sys
import os
import requests

# Get personal access token from env. variables
# Personal access token needs full repo rights.
GITHUB_PAT_KEY = 'PERSONAL_ACCESS_TOKEN'
GITHUB_PAT = os.getenv(GITHUB_PAT_KEY)
if GITHUB_PAT is None:
    sys.exit(f"{GITHUB_PAT_KEY} environment variable doesn't exist.")

# Modified requests item
r = requests.Session()
r.headers.update({'Authorization': f'Bearer {GITHUB_PAT}', 'User-Agent': 'dfar-io'})

# Configuration values
API_URL = "https://api.github.com/"
USER = "dfar-io"

def get_repos():
    '''
    Gets non-readonly repos from Github as a list of strings providing their name.
    https://docs.github.com/en/rest/reference/repos#list-organization-repositories
    '''
    try:
        response = r.get(f'{API_URL}users/{USER}/repos')
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        sys.exit(f'Error when getting repos ({response.status_code}): {response.text}')

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
        'allow_squash_merge': 'true',
        'allow_merge_commit': 'false',
        'allow_rebase_merge': 'false',
        'allow_auto_merge': 'false',
        'delete_branch_on_merge': 'true',
        'allow_update_branch': 'true'
    }
    try:
        response = r.patch(f'{API_URL}repos/{USER}/{repo}', json=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        sys.exit(f'Error when updating \'{repo}\' ({response.status_code}): {response.text}')

def update_branch_protection(branch, repo, has_build_job):
    '''
    Updates branch protections
    https://docs.github.com/en/rest/reference/branches#update-branch-protection
    '''

    required_status_checks = {
        'url': f'{API_URL}/repos/{USER}/{repo}/branches/{branch}/protection/required_status_checks',
        'strict': True,
        'checks': [{ 'context': 'build' }] if has_build_job else []
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
        response = r.put(f'{API_URL}repos/{USER}/{repo}/branches/{branch}/protection', json=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        sys.exit(
            'Error when updating branch protections for '
            + f'\'{repo}\':{branch} ({response.status_code}): {response.text}')

def branch_exists(branch, repo):
    '''
    Checks if a branch exists in a repo.
    https://docs.github.com/en/rest/reference/repos#list-organization-repositories
    '''
    response = r.get(f'{API_URL}repos/{USER}/{repo}/branches/{branch}')
    return response.status_code == 200

def contains_build_workflow_runs(repo):
    '''
    Checks if a repo contains 'build.yml' workflow runs
    https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository
    '''
    
    # Once eventhorizon is using a build step correctly, this should be removed. 2022.10.02
    if repo == 'eventhorizon':
        return False
    
    response = r.get(f'{API_URL}repos/{USER}/{repo}/actions/workflows/build.yml/runs')
    return response.status_code == 200

def main():
    '''Sets all repository settings to consistent settings'''
    repos = get_repos()
    for repo in repos:
        update_repo(repo)
        main_branch = 'main'

        has_build_job = contains_build_workflow_runs(repo)
        update_branch_protection(main_branch, repo, has_build_job)

        print(f'{repo : <30} {main_branch : <20}{has_build_job : <10}')


if __name__ == "__main__":
    main()