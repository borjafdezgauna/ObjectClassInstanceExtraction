import common.zenodoget


def download_files(doi, zenodo_access_token, output_dir = "data/xml"):

    downloaded_files = common.zenodoget.download(doi, output_dir, zenodo_access_token)
    print(f"Downloaded {len(downloaded_files)} file(s): {downloaded_files}")
    return downloaded_files
