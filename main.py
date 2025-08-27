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

def sanitize_folder_name(name):
    # Remove or replace forbidden characters for Windows folders
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def regularToAPI(rurl: str):
    print('[pillowcase] converting', rurl, 'to api url')
    return 'https://api.pillows.su/api/download/' + rurl.split('/')[-1]

def downloadRegular(url: str, folder: str):
    print(f'[pillowcase] registering download {url}...')
    url = regularToAPI(url)

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
                return filename
            except:
                print('[pillowcase] local download failure - check your internet status if this is concurrent')
                return 'Unavailable'
        else:
            return filename
    else:
        print("[pillowcase] failed to download, status:", r.status_code)
        return 'Unavailable'

def downloadEra(eraName, section):
    if eraName in eraNames:
        sectionName = os.path.splitext(os.path.basename(section))[0]
        folderName = f'{eraName}_{sectionName}'.replace(':', '-')
        baseFolderDir = f'./downloads/{folderName}'
        os.makedirs(baseFolderDir, exist_ok=True)
        print(f'Finding era {eraName} in section {sectionName} (This may take a while)...')
        for i in range(1, sum(1 for _ in open(section, encoding="utf8"))):
            data, type = tsv.getLine(i, section)
            # Only process songs that match the selected era
            if type == 'song' and data['Era'] == eraName:
                print(f'Indexed entry: {data["Name"]}')
                song_name_sanitized = sanitize_folder_name(data['Name'])
                song_folder = os.path.join(baseFolderDir, song_name_sanitized)
                os.makedirs(song_folder, exist_ok=True)
                for link in data['Links']:
                    if str(link).startswith('https://pillows.su/f/'):
                        fn = downloadRegular(link, song_folder)
    else:
        print('invalid era given')
                

if __name__ == '__main__':
    era, _ = pick.pick(eraNames, 'Select an era to archive:')
    file, _ = pick.pick(glob.glob("tracker-tabs/*.tsv"), 'Pick a section:')
    downloadEra(era, file)
    print('[main] Finished!')