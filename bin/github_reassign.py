#!/usr/bin/env python3

import click
import requests

# Constants
BASE_URL = "https://api.github.com"
HEADERS = {
    "Authorization": "token YOUR_PERSONAL_ACCESS_TOKEN",
    "Accept": "application/vnd.github.v3+json"
}

def get_repos_with_assigned_issues(user):
    """
    Get repositories with open issues and PRs assigned to the user.

    :param user: Username of the person whose assigned issues/PRs you want to fetch.
    :return: Set of repositories.
    """
    page = 1
    repos = set()

    while True:
        # Fetch issues assigned to `user`
        issues_url = f"{BASE_URL}/search/issues?q=assignee:{user}+is:open&page={page}&per_page=100"
        response = requests.get(issues_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Check if we have results
        if not data.get('items'):
            break

        for issue in data['items']:
            repos.add('/'.join(issue['repository_url'].split('/')[-2:]))

        # Check if there's a next page
        if 'next' not in response.links:
            break

        page += 1

    return repos


def reassign_issues_and_prs(from_user, to_user, dry_run, repo):
    """
    Reassign issues and PRs from one user to another.

    :param from_user: Username of the person from whom you want to reassign.
    :param to_user: Username of the person to whom you want to reassign.
    """
    if repo:
        repos = [repo]
    else:
        repos = sorted(get_repos_with_assigned_issues(from_user))

    for repo in repos:
        # Fetch issues assigned to `from_user`
        issues_url = f"{BASE_URL}/repos/{repo}/issues?assignee={from_user}&state=open"
        response = requests.get(issues_url, headers=HEADERS)
        response.raise_for_status()
        issues = response.json()

        for issue in issues:
            # Reassign issue

            issue_url = f"{BASE_URL}/repos/{repo}/issues/{issue['number']}"
            data = {
                "assignees": [to_user]
            }

            if not is_collaborator(repo, to_user):
                print(f"Would need to invite {to_user} to https://github.com/{repo}/settings/access")
                if not dry_run:
                    if True: # DOES NOT WORK -- 404 :-/  invite_user(repo, to_user):
                        click.pause(info=f'Press Enter to continue when invitation was accepted at '
                                         f'https://github.com/{repo}/invitations ...')

            if dry_run:
                print(f"Would send request to {issue_url} with data {data} and headers {HEADERS}")
                continue

            response = requests.patch(issue_url, json=data, headers=HEADERS)
            if response.status_code == 200:
                print(f"Issue #{issue['number']} in {repo} reassigned to {to_user}")
            else:
                print(f"Failed to reassign issue #{issue['number']} in {repo}: "
                      f"{response.reason} - {response.json()['message']}")


def is_collaborator(repo, user):
    """Check if a user is a collaborator in a repository."""
    url = f"{BASE_URL}/repos/{repo}/collaborators/{user}"
    response = requests.get(url, headers=HEADERS)
    return response.status_code == 204  # 204 No Content means the user is a collaborator


def invite_user(repo, user):
    """Invite a user to a repository with Write permissions."""
    url = f"{BASE_URL}/repos/{repo}/collaborators/{user}"
    data = {
        "permission": "write"
    }
    # headers_ = HEADERS.copy()
    # headers_['Accept'] = 'application/vnd.github+json'  # recommended
    response = requests.put(url, headers=HEADERS, json=data)
    if response.status_code == 201:  # 201 Created means the invitation was successfully sent
        click.echo(f"Invited {user} to {repo} with Write permissions.")
        return True
    else:
        import pdb; pdb.set_trace()
        click.echo(f"Failed with {response.status_code} to invite {user} to {repo}. Error: {response.json()}")
        return False


# def ensure_collaborator(repo, user):
#     """Ensure a user is a collaborator in a repository. If not, invite them."""
#     if not is_collaborator(repo, user):
#         return invite_user(repo, user)
#     else:
#         return None  # already collaborator
#

@click.group()
@click.option('--token', prompt='GitHub Personal Access Token', help='Your GitHub Personal Access Token.',
              hide_input=True)
def cli(token):
    if token:
        HEADERS["Authorization"] = f"token {token}"


@cli.command()
@click.option('--from-user', prompt='From User', help='Username of the person from whom you want to reassign.')
@click.option('--to-user', prompt='To User', help='Username of the person to whom you want to reassign.')
@click.option('-n', '--dry-run', is_flag=True, help='Do not do modifications - just show what will be done')
@click.option('--repo', help='Just work on a given repository')
def reassign(from_user, to_user, dry_run, repo):
    reassign_issues_and_prs(from_user, to_user, dry_run, repo)


@cli.command()
@click.argument('user') # , help='Username of the person from whom you want to reassign.')
def list_repos(user):
    for repo in sorted(get_repos_with_assigned_issues(user)):
        print(repo)


if __name__ == "__main__":
    cli()
