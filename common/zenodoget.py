#!/usr/bin/env python3
from contextlib import contextmanager
from fnmatch import fnmatch
import hashlib
from importlib.metadata import version
import os
import sys
from urllib.parse import unquote

import requests
import wget



def check_hash(filename, checksum):
    algorithm = "md5"
    value = checksum.strip()
    if not os.path.exists(filename):
        return value, "invalid"
    h = hashlib.new(algorithm)
    with open(filename, "rb") as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            h.update(data)
    digest = h.hexdigest()
    return value, digest


def download(doi, output_dir, access_token):
    url = doi
    if not url.startswith("http"):
        url = "https://doi.org/" + url
    try:
        r = requests.get(url, timeout=1000)
    except requests.exceptions.ConnectTimeout:
        print("Connection timeout.")
        sys.exit(1)
    except Exception:
        print("Connection error.")
        sys.exit(1)
    if not r.ok:
        print("DOI could not be resolved. Try again, or use record ID.")
        sys.exit(1)

    recordID = r.url.split("/")[-1]
    url = "https://zenodo.org/api/records/"
    params = {}
    if access_token is not None:
        params["access_token"] = access_token

        try:
            r = requests.get(url + recordID, params=params, timeout=5000)
        except requests.exceptions.ConnectTimeout:
            print("Connection timeout during metadata reading.")
            sys.exit(1)
        except Exception:
            print("Connection error during metadata reading.")
            sys.exit(1)

        if r.ok:
            js = r.json()
            files = js["files"]
            if not files:
                print("Files not found in metadata")

            total_size = sum((f.get("filesize") or f["size"]) for f in files)

        
            print("Title: {}".format(js["metadata"]["title"]))
            print("Keywords: " + (", ".join(js["metadata"].get("keywords", []))))
            print("Publication date: " + js["metadata"]["publication_date"])
            print("DOI: " + js["metadata"]["doi"])
            print(f"Total size: {total_size/1024/1024} Mb")

            downloaded = []
            for f in files:
                fname = f.get("filename") or f["key"]
                link = "https://zenodo.org/records/{}/files/{}".format(recordID, fname)

                size = f.get("filesize") or f["size"]
                print()
                print(f"Link: {link}   size: {size}")
                fname = f.get("filename") or f["key"]
                local_file = os.path.join(output_dir, fname)

                checksum = f["checksum"].split(":")[-1]

                if os.path.exists(local_file):
                    
                    remote_hash, local_hash = check_hash(local_file, checksum)

                    if remote_hash == local_hash:
                        print(f"{fname} is already downloaded correctly.")
                        downloaded.append(local_file)
                        continue
            
                try:
                    link = f.get("links").get("self")
                    link = f"{link}?access_token={access_token}"
                    if (not os.path.exists(output_dir)):
                        os.mkdir(output_dir)
                    filename = wget.download(link, out= local_file)
                    
                except Exception:
                    print(f"  Download error. Original link: {link}")
           
                h1, h2 = check_hash(filename, checksum)
                if h1 == h2:
                    print(f"Checksum is correct. ({h1})")
                    downloaded.append(filename)
                else:
                    print(f"Checksum is INCORRECT!({h1} got:{h2})")
                    os.remove(filename)
                    print("  File is deleted.")
            
            print("\nAll files have been downloaded.")
            return downloaded
        else:
            print("Record could not get accessed.")
            sys.exit(1)

if __name__ == '__main__':
    downloaded = download(sys.argv[1], sys.argv[2], sys.argv[3])
    print(downloaded)