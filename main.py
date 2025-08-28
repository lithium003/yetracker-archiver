# regular link: https://pillows.su/f/91dd7af71aa25742baa974f98e5994a0
# api link: https://api.pillows.su/api/download/91dd7af71aa25742baa974f98e5994a0 (.mp3)

import pick
import glob
import requests
import re
import os
import tsv
from data import eraNames
from tqdm import tqdm

"""
Removes illegal characters from folder names to avoid Windows errors.
Args:
    name (str): The folder name to sanitize.

Returns:
    str: The sanitized folder name.
"""
def sanitize_name(name: str) -> str:
    # Truncate name after 50 characters to avoid exceeding the 256-char path limit on save
    trimmed_name = name[:50]
    # Prevent folder from ending with a dot
    if trimmed_name[-1] == '.':
        trimmed_name = trimmed_name[:-1] + '_'
    # Remove or replace forbidden characters for Windows folders
    sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', trimmed_name).strip()
    return sanitized_name

"""
Converts a regular download URL to a Pillowcase API download URL.
Args:
    rurl (str): The regular download URL.

Returns:
    str: The API download URL.
"""
def regularToAPI(rurl: str):
    print('[pillowcase] converting', rurl, 'to api url')
    return 'https://api.pillows.su/api/download/' + rurl.split('/')[-1]

"""
Handles a url for downloading.
Args:
    url (str): The download URL.
    folder (str): The folder to save the downloaded file.
"""
def downloadRegular(url: str, folder: str):
    # Handle multiple links together
    split = url.split(' ')
    if len(split) > 1:
        print(f'[System] Found multiple links in {url}, registering all...')
        for link in split:
            downloadRegular(link, folder)
        return

    if 'pillows.' in url:
        # Handle Pillowcase links
        print(f'[pillowcase] registering download {url}...')
        url = regularToAPI(url)
    else:
        # Handle other links
        print(f'[Other] Non-pillowcase link at {url}, skipping download, saving link.')
        with open(f'{folder}/external_links.txt', 'a') as f:
            f.write(url + '\n')
        return
    
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        cd = r.headers.get("content-disposition")
        if cd:
            filename = re.findall('filename="?(.+)"?', cd)[0].strip('"')
        else:
            filename = os.path.basename(url)

        filename = f'{folder}/{filename}'

        if not os.path.exists(filename):
            try:
                size = int(r.headers.get('content-length', 0))
                print(f'[pillowcase] downloading {filename}...')
                bar = tqdm(total=size, unit='iB', unit_scale=True)
                with open(filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        bar.update(len(chunk))
                bar.close()

                print(f"[pillowcase] downloaded as: {filename}")
                return
            except:
                print('[pillowcase] local download failure - check your internet status if this is concurrent')
                with open(f'{folder}/external_links.txt', 'a') as f:
                    f.write('DOWNLOAD FAILED: ' + url + '\n')
                return
        else:
            return
    else:
        print("[pillowcase] failed to download, status:", r.status_code)
        return

def downloadEra(eraName, section):
    if eraName in eraNames:
        sectionName = sanitize_name(os.path.splitext(os.path.basename(section))[0])
        folderName = sanitize_name(eraName)
        folderDir = f'./downloads/{sectionName}/{folderName}'
        os.makedirs(folderDir, exist_ok=True)
        print(f'Finding era {eraName} in section {sectionName} (This may take a while)...')
        for i in range(1, sum(1 for _ in open(section, encoding="utf8"))):
            data, type = tsv.getLine(i, section)
            # Only process songs that match the selected era
            if type == 'song' and data['Era'] == eraName:
                print(f'Indexed entry: {data["Name"]}')
                song_name_clean = sanitize_name(data['Name'])
                song_folder = os.path.join(folderDir, song_name_clean)
                os.makedirs(song_folder, exist_ok=True)
                for link in data['Links']:
                    downloadRegular(link, song_folder)
    else:
        print('invalid era given')
                

if __name__ == '__main__':
    era, _ = pick.pick(eraNames, 'Select an era to archive:')
    file, _ = pick.pick(glob.glob("tracker-tabs/*.tsv"), 'Pick a section:')
    cont, _ = pick.pick(['Yes', 'No'], f'Archive all eras after {era} as well? (This may take a LONG while)')    
    if cont == 'Yes':
        cutoff = eraNames.index(era)
        for era in eraNames:
            if era in eraNames[:cutoff]:
                continue
            downloadEra(era, file)
    else:
        downloadEra(era, file)
    print('[main] Finished!')