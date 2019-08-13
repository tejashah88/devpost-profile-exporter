#!/usr/bin/env python3

import re
from copy import copy
import json
import os

from bs4 import BeautifulSoup
import click
import requests
from html2text import html2text

from async_utils import AsyncProgressBar

VALID_FORMATS = ['text', 'json']

# Source: https://stackoverflow.com/a/46890853
from functools import reduce
def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)

def generate_bullet_list(lst, indent=2, bullet='-'):
    result = '\n'
    if lst is None:
        return None
    for item in lst:
        result += ' ' * indent + bullet + ' ' + item + '\n'
    return result.rstrip()

def get_soup(url):
    req = requests.get(url)

    # raise an error if it's not an OK response
    req.raise_for_status()

    return BeautifulSoup(req.content, 'html.parser')

def get_project_info(project_link):
    project_id = project_link[len('https://devpost.com/software/'):]

    try:
        project_soup = get_soup(project_link)
    except Exception as err:
        click.echo(f"\nEncountered an error while trying to access project '{project_id}':")
        click.echo(err)
        return { 'id': project_id, 'link': project_link, 'error': err }

    title = project_soup.find(id='app-title').text

    short_desc_wrapper = project_soup.find(class_='large')
    short_desc = None
    if short_desc_wrapper is not None:
        short_desc = short_desc_wrapper.text.strip()

    # retrieve the long description text (in markdown)
    long_desc_wrapper = copy(project_soup.find(id='app-details-left'))

    # remove gallery and built with to get original long description
    gallery_tmp = long_desc_wrapper.find(id='gallery')
    if gallery_tmp is not None:
        gallery_tmp.decompose()

    built_with_tmp = long_desc_wrapper.find(id='built-with') # .find(id='built-with').find_previous('div')
    if built_with_tmp is not None:
        built_with_tmp.decompose()

    long_desc_html = long_desc_wrapper.prettify()
    long_desc_markdown = html2text(long_desc_html)

    # determine number of likes
    like_btn = project_soup.find(class_='software-likes')
    like_count_tag = like_btn.find(class_='side-count')
    like_count = 0 if like_count_tag is None else int(like_count_tag.text)

    # determine number of comments
    comment_btn = project_soup.find(id='software-comment-button')
    comment_count_tag = comment_btn.find(class_='side-count')
    comment_count = 0 if comment_count_tag is None else int(comment_count_tag.text)

    # determine team members
    team_members_wrapper = project_soup.find_all(class_='software-team-member')
    team_members_html = [wrapper.find_all(class_='user-profile-link')[1] for wrapper in team_members_wrapper]
    team_members = [{
        'name': member_html.text,
        'username': member_html['href'][len('https://devpost.com/'):] # we only want to store the username
    } for member_html in team_members_html]

    # determine the hackathon that the project was submitted to
    hackathon_wrapper = project_soup.find(class_='software-list-content')
    hackathon_info = None

    # NOTE: if 'hackathon_wrapper' is None, then hackathon is not visible for not logged in users
    if hackathon_wrapper is not None:
        hackathon_unwrapped = hackathon_wrapper.p.a
        hackathon_info = {
            'name': hackathon_unwrapped.text,
            'link': hackathon_unwrapped['href']
        }

    # determine what prizes (if applicable) the project won
    prizes_wrapper = project_soup.find(class_='software-list-content')
    awards = None
    if prizes_wrapper is not None and prizes_wrapper.ul is not None:  # we got a winner!
        awards = []
        # this mess is literally because apparently you can't just get the text content without adjacent tags
        # all it does is split by newlines, filter wordless and 'Winner' strings, and gets the longest string
        awards_groups = [prize_part.text.split('\n') for prize_part in prizes_wrapper.ul.find_all('li')]
        for info_group in awards_groups:
            cleaned_parts = [part.strip() for part in info_group]
            filtered_parts = [part for part in cleaned_parts if part != 'Winner' or len(part) == 0]
            awards += [sorted(filtered_parts, key=len, reverse=True)[0]]

    # determine what the project was "Built With"
    built_with_wrapper = project_soup.find(id='built-with')
    built_with = None
    if built_with_wrapper is not None:
        built_with = [bw_obj.text for bw_obj in built_with_wrapper.find_all(class_='cp-tag')]

    # determine any links that are related to the project ("Try It Out" section)
    try_it_out_wrapper = project_soup.find(class_='app-links')
    relevant_links = None
    if try_it_out_wrapper is not None:
        tmp_links = try_it_out_wrapper.find_all('a')
        relevant_links = [link['href'] for link in tmp_links]

    project_info = {
        'title': title,
        'id': project_id,
        'link': project_link,
        'short-description': short_desc,
        'long-description': long_desc_markdown,
        'likes': like_count,
        'comments': comment_count,
        'team-members': team_members,
        'hackathon': hackathon_info,
        'awards': awards,
        'built-with': built_with,
        'relevant-links': relevant_links
    }

    return project_info

def get_all_project_links(username):
    page_number = 1
    project_links = []

    while True:
        click.echo(f"Scraping projects from page {page_number} of {username}'s profile...", nl=False)

        # find all links that match the project URl format (https://devpost.com/software/example-project-id)
        profile_soup = get_soup(f'https://devpost.com/{username}?page={page_number}')
        project_blobs = profile_soup.find_all('a', href=re.compile('^https:\/\/devpost\.com\/software\/(.+)$'))

        tmp_links = [project_blob['href'] for project_blob in project_blobs if not 'built-with' in project_blob['href']]
        project_links += tmp_links

        click.echo(f'found {len(tmp_links)} projects!')

        # check if there's more projects to scrape their links
        more_projects_button = profile_soup.find(class_='next_page')
        if more_projects_button is None:    # user has <= 24 projects
            break
        else:
            next_link_suburl = more_projects_button.a['href']
            if next_link_suburl == '#':     # we are at the end of the pagination
                break
            else:
                page_number += 1

    click.echo(f'Found a total of {len(project_links)} projects!')
    return project_links

def save_to_format(project_info_list, output_folder, out_format):
    # generate output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    def save_to_json(project_info, filename, output_folder):
        with open(f'{output_folder}/{filename}.json', 'w', encoding='utf-8') as outfile:
            json.dump(project_info, outfile, indent=4, ensure_ascii=False)

    def save_to_text(project_info, filename, output_folder):
        team_members = 'Unknown' if project_info['team-members'] is None else [ member["name"] for member in project_info["team-members"] ]
        hackathon_name = deep_get(project_info, "hackathon.name") or 'Unknown'
        with open(f'{output_folder}/{filename}.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(f'Title: {project_info.get("title", "N/A")}\n\n')
            outfile.write(f'Project ID: {project_info.get("id", "N/A")}\n\n')
            outfile.write(f'Project Link: {project_info.get("link", "N/A")}\n\n')
            outfile.write(f'Short Description: {project_info.get("short-description", "N/A")}\n\n')
            outfile.write(f'# of Likes: {project_info.get("likes", "N/A")}\n\n')
            outfile.write(f'# of Comments: {project_info.get("comments", "N/A")}\n\n')
            outfile.write(f'Team Members: {generate_bullet_list(team_members)}\n\n')
            outfile.write(f'Hackathon submitted to: {hackathon_name}\n\n')
            outfile.write(f'Awards Won: {generate_bullet_list(project_info.get("awards", "N/A"))}\n\n')
            outfile.write(f'Built with: {generate_bullet_list(project_info.get("built-with", "N/A"))}\n\n')
            outfile.write(f'Relevant Links: {generate_bullet_list(project_info.get("relevant-links", "N/A"))}\n\n')
            outfile.write('Long description:\n\n')
            outfile.write(project_info.get('long-description', 'N/A').rstrip())

    save_fns = { 'json': save_to_json, 'text': save_to_text }
    filtered_info_list = [ project_info for project_info in project_info_list if project_info.get('error') is None ]
    with click.progressbar(filtered_info_list, label='Saving projects') as bar:
        for project_info in bar:
            save_fns[out_format](project_info, project_info['title'], output_folder)

@click.command()
@click.argument('username', metavar='<username>')
@click.argument('output_format', metavar='<output-format>')
@click.option('--output-folder', 'output_folder', metavar='<output-folder>', help='The output folder to store all projects')
def cli(username, output_format, output_folder):
    '''
    This CLI tool takes a valid Devpost username and scrapes
    all the user's projects and the corresponding information.
    The projects will be outputted into a folder with all the
    project details in the specified format.

    \b
    - <username> = The Devpost username
    - <output-format> = One of the valid output formats for saving the projects
      - valid formats: text, json
      - NOTE: The 'text' format will not save links for team members and hackathons
    - <output-folder> = The output folder to store all projects. By default, it
                        saves all projects to '<username>-projects/'
    '''

    # check if given format is an acceptable format
    if output_format not in VALID_FORMATS:
        click.echo(f"Invalid output format provided: '{output_format}'", err=True)
        return

    # retrieve/construct the url for the user's profile
    profile_link = None
    if username is not None:
        profile_link = f'https://devpost.com/{username}?page=1'

    # check if it's a real Devpost profile
    profile_req = requests.get(profile_link)

    # show an error if the user profile doesn't exist
    if profile_req.status_code != requests.codes.ok:
        click.echo(f"User '{username}' doesn't exist!", err=True)
        return

    # grab all project links from the user profile
    project_links = get_all_project_links(username)

    abar = AsyncProgressBar(max_workers=16)
    # we parallelize this process since HTTP requests are blocking by nature

    project_info_list = abar.process(project_links, get_project_info, 'Scraping project infos')

    # no need to parallelize this part since the max measured time was 20 ms
    # for 60+ projects in the json format (try yosun's profile)
    save_to_format(project_info_list, output_folder or f'{username}-projects', output_format)

if __name__ == '__main__':
    cli()