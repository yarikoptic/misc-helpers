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
        data = response.json()

        # Check if we have results
        if not data.get('items'):
            break

        for issue in data['items']:
            repos.add(issue['repository_url'].split('/')[-1])

        # Check if there's a next page
        if 'next' not in response.links:
            break

        page += 1

    return repos

def reassign_issues_and_prs(from_user, to_user):
    """
    Reassign issues and PRs from one user to another.

    :param from_user: Username of the person from whom you want to reassign.
    :param to_user: Username of the person to whom you want to reassign.
    """
    repos = get_repos_with_assigned_issues(from_user)

    for repo in repos:
        # Fetch issues assigned to `from_user`
        issues_url = f"{BASE_URL}/repos/{repo}/issues?assignee={from_user}&state=open"
        response = requests.get(issues_url, headers=HEADERS)
        issues = response.json()

        for issue in issues:
            # Reassign issue
            issue_url = f"{BASE_URL}/repos/{repo}/issues/{issue['number']}"
            data = {
                "assignees": [to_user]
            }
            response = requests.patch(issue_url, json=data, headers=HEADERS)
            if response.status_code == 200:
                print(f"Issue #{issue['number']} in {repo} reassigned to {to_user}")
            else:
                print(f"Failed to reassign issue #{issue['number']} in {repo}")

if __name__ == "__main__":
    # Replace with your details
    FROM_USER = "old_user"
    TO_USER = "new_user"

    reassign_issues_and_prs(FROM_USER, TO_USER)
