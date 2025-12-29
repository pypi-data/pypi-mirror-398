import gdown, gzip, shutil, os, tarfile
import zipfile
from .bistack import _pip_install, _pkg_base_name, _get_dist_version

ANNDATA_ = True
try:
    import anndata 
except ImportError:
    spec = 'anndata'
    upgrade = False
    base = _pkg_base_name(spec)
    cur_v = _get_dist_version(base)

    if cur_v:
        print(f"{base}: already installed (v{cur_v})")
    else:
        rc = _pip_install(spec, quiet=True, upgrade=upgrade)
        new_v = _get_dist_version(base)
        if rc == 0 and new_v:
            tag = "upgraded" if (cur_v and upgrade) else "installed"
            print(f"{base}: {tag} (v{new_v})")
        else:
            print(f"WARNING: {base} install failed")
            ANNDATA_ = False


def download_from_google_drive( file_id, out_path = 'downloaded' ):
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    gdown.download(url, out_path, quiet = False)
    return out_path

def decompress_gz( file_in, file_out, remove_gz = True ):
    try:
        with gzip.open(file_in, 'rb') as f_in:
            with open(file_out, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                if remove_gz:
                    os.remove(file_in)
                print(f'File saved to: {file_out}')
                return file_out
    except:
        return None


def decompress_zip(file_in, extract_dir = './', remove_zip = True ):
    try:
        with zipfile.ZipFile(file_in, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            if remove_zip:
                os.remove(file_in)
            print(f'Files extracted to: {extract_dir}')
            return extract_dir
    except:
        return None


def decompress_zip_and_move(file_in, extract_dir='temp_extract', remove_zip=True):
    try:
        with zipfile.ZipFile(file_in, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = zip_ref.namelist()

        if len(extracted_files) != 1:
            print("Zip 파일에 하나 이상의 파일이 포함되어 있습니다.")
            return None

        # 압축 해제된 파일 경로
        extracted_path = os.path.join(extract_dir, extracted_files[0])

        # 이동 대상 경로 (현재 작업 디렉토리로 이동)
        file_out = os.path.basename(extracted_files[0])
        shutil.move(extracted_path, file_out)

        # 압축 해제 폴더 및 zip 파일 제거 (옵션)
        if remove_zip:
            os.remove(file_in)
        shutil.rmtree(extract_dir)

        return file_out

    except Exception as e:
        print(f"오류 발생: {e}")
        return None


def decompress_tar_gz( file_in, remove_org = True ):

    try:
        extract_path = 'extract_tmp'
        if os.path.isdir(extract_path):
            shutil.rmtree(extract_path)
    
        with tarfile.open(file_in, "r:gz") as tar:
            tar.extractall(path=extract_path)
    
        file_h5ad = os.listdir(extract_path)[0]
        file = extract_path + '/%s' % file_h5ad
        if os.path.isdir(file):
            file_h5ad = os.listdir(file)[0]
            file = file + '/%s' % (file_h5ad)
    
        if os.path.isfile(file_h5ad):
            os.remove(file_h5ad)
    
        if not os.path.isfile(file_h5ad):
           shutil.move(file, '.')
    
        shutil.rmtree(extract_path)
        if remove_org:
            os.remove(file_in)
    
        print(f'File saved to: {file_h5ad}')
        return file_h5ad
    except:
        return None


sample_data_fid_dict = {
    'Lung':       '1yMM4eXAdhRDJdyloHACP46TNCpVFnjqD', 
    'NSCLC':      '1yMM4eXAdhRDJdyloHACP46TNCpVFnjqD',
    'Intestine':  '1oz1USuvIT7VNSmS2WhJuHDZQhkCH6IPY', 
    'Colon':      '1oz1USuvIT7VNSmS2WhJuHDZQhkCH6IPY', 
    'CRC':        '1oz1USuvIT7VNSmS2WhJuHDZQhkCH6IPY',
    'Breast':     '158LUiHiJNFzYvqY-QzMUm5cvIznBrUAV', 
    'BRCA':       '158LUiHiJNFzYvqY-QzMUm5cvIznBrUAV',
    'Pancreas':   '1OgTsyXczHQoV6PJyo_rfNBDJRRHXRhb-', 
    'PDAC':       '1OgTsyXczHQoV6PJyo_rfNBDJRRHXRhb-', 
    'Colitis-mm': '11cVrrxaeai87pKKiUcSjCd-Lw7hkrzrI', 
    'Colitis-hs': '12641IgY-cidvomm4ZZziAcTplYngaq0C', 
    'Melanoma':   '1hlGXEi9UEIZiHGHZJgxZPClVsPdHpvZS'
}

def load_h5ad( tissue, file_type = 'gz' ):

    tlst = list(sample_data_fid_dict.keys())

    if tissue in tlst:
        file_id = sample_data_fid_dict[tissue]
    else:
        print('tissue must be one of %s. ' % ', '.join(tlst))
        return None

    file_h5ad = None
    file_down = download_from_google_drive( file_id )
    # file_h5ad = decompress_gz( file_down, '%s.h5ad' % tissue, remove_gz = True )
    if file_type == 'tar.gz':
        file_h5ad = decompress_tar_gz( file_down, remove_org = True )    
        adata = anndata.read_h5ad(file_h5ad)
    elif file_type == 'gz':
        file_h5ad = decompress_gz( file_down, '%s.h5ad' % tissue, remove_gz = True )
        adata = anndata.read_h5ad(file_h5ad)
    elif file_type == 'zip':
        file_h5ad = decompress_zip_and_move(file_down, remove_zip=True)
        adata = anndata.read_h5ad(file_h5ad)

    return file_h5ad


def load_anndata( tissue ):

    file_h5ad = load_h5ad( tissue )
    if file_h5ad is None:
        return None
    else:
        adata = anndata.read_h5ad(file_h5ad)
        return adata


def load_sample_data( file_id_or_tissue_name, file_type = 'tar.gz' ):

    tlst = list(sample_data_fid_dict.keys())
    
    if file_id_or_tissue_name in tlst:
        return load_anndata( file_id_or_tissue_name )
    else:
        adata = None
        try:
            file_down = download_from_google_drive( file_id_or_tissue_name )
        except:
            print('ERROR: The file_id you requested does not exist.')
            print('You can try one of %s. ' % ', '.join(tlst))
            return None

        file_h5ad = None
        if file_type == 'tar.gz':
            file_h5ad = decompress_tar_gz( file_down, remove_org = True )   
                
        elif file_type == 'gz':
            file_h5ad = decompress_gz( file_down, 'downloaded.h5ad', remove_gz = True )

        elif file_type == 'zip':
            file_h5ad = decompress_zip_and_move(file_down, remove_zip=True)
        
        if file_h5ad is None:
            print('ERROR: The file_type might be a wrong one.')
            print('You can try with one of tar.gz or gz for file_type argument. ')
            print('Or, You can try one of %s for file_id_or_tissue_name. ' % ', '.join(tlst))
            return None
        else:
            try:
                adata = anndata.read_h5ad(file_h5ad)
            except:
                print('ERROR: Cannot read the downloaded file.')
                print('You can try one of %s for file_id_or_tissue_name. ' % ', '.join(tlst))
                return None
                
        return adata

processed_sample_data_fid_dict = {
    'Lung':       '1Xazyv4JhWlhYkDVk51KXaL3DDlAoxftp', 
    'NSCLC':      '1Xazyv4JhWlhYkDVk51KXaL3DDlAoxftp',
    'Intestine':  '1Xb_dzJDgt_RlkXk5nP0jgRUz_aFdP0G9', 
    'Colon':      '1Xb_dzJDgt_RlkXk5nP0jgRUz_aFdP0G9', 
    'CRC':        '1Xb_dzJDgt_RlkXk5nP0jgRUz_aFdP0G9',
    'Breast':     '1XbX8Q3dH1kOWnM6ppms4BR2ukEAKYisB', 
    'BRCA':       '1XbX8Q3dH1kOWnM6ppms4BR2ukEAKYisB',
    'Pancreas':   '1XbYJQpyo8PaoL_vpjBt4YI5tTi8pgV5o', 
    'PDAC':       '1XbYJQpyo8PaoL_vpjBt4YI5tTi8pgV5o', 
    'Colitis-mm': '1QgdmySeTYQjW0NfNxbpaokU22VpEpcHA', 
    'Colitis-hs': '1qRjo2iPlDVxF88umvpxiNGXk6jFK9dbb' 
}

def load_scoda_processed_anndata( tissue = None, file_type = 'tar.gz' ):

    tlst = list(processed_sample_data_fid_dict.keys())

    if tissue in tlst:
        file_id = processed_sample_data_fid_dict[tissue]
    else:
        print('tissue must be one of %s. ' % ', '.join(tlst))
        return None

    file_h5ad = None
    try:
        file_down = download_from_google_drive( file_id )
        if file_type == 'tar.gz':
            file_h5ad = decompress_tar_gz( file_down, remove_org = True )
        elif file_type == 'gz':
            file_h5ad = decompress_gz( file_down, '%s.h5ad' % tissue, remove_gz = True )
        elif file_type == 'zip':
            file_h5ad = decompress_zip_and_move(file_down, remove_zip=True)
            
    except:
        pass

    if file_h5ad is None:
        return None
    else:
        adata = anndata.read_h5ad(file_h5ad)
        return adata


def load_scoda_processed_sample_data( file_id_or_tissue_name = None, file_type = 'tar.gz' ):

    file_type = 'tar.gz'
    tlst = list(processed_sample_data_fid_dict.keys())

    if file_id_or_tissue_name in tlst:
        return load_scoda_processed_anndata( file_id_or_tissue_name, file_type )
    else:
        adata = None
        try:
            file_down = download_from_google_drive( file_id_or_tissue_name )
        except:
            print('ERROR: The file_id you requested does not exist.')
            print('You can try one of %s. ' % ', '.join(tlst))
            return None

        if file_type == 'tar.gz':
            file_h5ad = decompress_tar_gz( file_down, remove_org = True )    
            adata = anndata.read_h5ad(file_h5ad)
        elif file_type == 'gz':
            file_h5ad = decompress_gz( file_down, 'downloaded.h5ad', remove_gz = True )
            adata = anndata.read_h5ad(file_h5ad)
        elif file_type == 'zip':
            file_h5ad = decompress_zip_and_move(file_down, remove_zip=True)
            adata = anndata.read_h5ad(file_h5ad)

        print('ERROR: The file_type might be a wrong one.')
        print('You can try with one of tar.gz or gz for file_type argument. ')
        print('Or, You can try one of %s for file_id_or_tissue_name. ' % ', '.join(tlst))
        return None
            
        return adata


def decompress_zip_folder(file_in, extract_dir='temp_extract', remove_zip=True):
    """
    ZIP 파일을 해제한 후,
    압축 해제된 최상위 폴더(또는 파일)를 현재 작업 디렉토리로 이동시키고 
    임시 폴더를 삭제하는 함수.
    """

    try:
        # 기존 temp 폴더 제거
        if os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir)

        # zip 파일 해제
        with zipfile.ZipFile(file_in, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # temp 폴더 안의 최상위 요소들 확인
        extracted_items = os.listdir(extract_dir)

        if len(extracted_items) == 0:
            print("압축 해제 폴더가 비어 있습니다.")
            return None

        # 이동할 최상위 항목 (보통 폴더 또는 단일 파일)
        for item in extracted_items:
            top_item = item
            src_path = os.path.join(extract_dir, top_item)
    
            # 동일한 이름의 폴더 또는 파일이 현재 경로에 이미 있다면 삭제
            if os.path.exists(top_item):
                if os.path.isdir(top_item):
                    shutil.rmtree(top_item)
                else:
                    os.remove(top_item)

            # 현재 디렉토리로 이동
            shutil.move(src_path, '.')

        # temp 폴더 제거
        shutil.rmtree(extract_dir)

        # zip 원본 파일 제거 옵션
        if remove_zip:
            os.remove(file_in)

        print(f"Extracted to: {top_item}")
        return top_item

    except Exception as e:
        print(f"오류 발생: {e}")
        return None


def decompress_tar_gz_folder(file_in, remove_org=True):
    """
    tar.gz 파일을 해제한 후,
    최상위 폴더를 현재 작업 디렉토리로 이동시키고
    임시폴더는 삭제하는 함수.
    """

    try:
        extract_path = 'extract_tmp'

        # 기존 임시 폴더 있으면 삭제
        if os.path.isdir(extract_path):
            shutil.rmtree(extract_path)

        # tar.gz 해제
        with tarfile.open(file_in, "r:gz") as tar:
            tar.extractall(path=extract_path)

        # 해제된 폴더(또는 파일) 목록 확인
        items = os.listdir(extract_path)
        if len(items) == 0:
            print("Error: Extracted folder is empty.")
            return None

        # 풀린 첫 번째 항목 (보통 최상위 폴더)
        for item in items:
            top_item = item
            src_path = os.path.join(extract_path, top_item)
    
            # 현재 폴더로 이동 (같은 이름 존재하면 에러 방지)
            # if os.path.exists(top_item):
            #     shutil.rmtree(top_item)  # 기존 폴더 삭제
            if os.path.exists(top_item):
                if os.path.isdir(top_item):
                    shutil.rmtree(top_item)
                else:
                    os.remove(top_item)
                
            shutil.move(src_path, '.')

        # 임시 해제 폴더 삭제
        shutil.rmtree(extract_path)

        # 원본 tar.gz 삭제 옵션
        if remove_org:
            os.remove(file_in)

        print(f"Folder extracted to: {top_item}")
        return top_item

    except Exception as e:
        print(f"Error: {e}")
        return None


bi_sample_data_fid_dict = {
    'RefGenome_hg38_sel':             '1uIHwlS3N4TsN7sJdD3j5Hf8B_clTQXHl',
    'Files_for_GATK_chr12':           '1pbMIMvoqBqGE9yMKUg2E-f2m4P8mmN4Y',  
    'Files_for_GATK':                 '13qwSu1e7d7olhKmpEuZYLSNShNCXfLkH',    
    'WES_PDAC_chr12': 		          '1l88p48edaw7oHTSdCFQgXALoUAdYr2nT',
    'WES_PDAC_chr12_bam': 	          '1xCiTuVPqLytx5NTxmaIQcLXoUGPP-XZ7',
    'WES_PDAC_chr12_SNV_CNV_results': '1V1tQQaMinXQvnjYT5y8FkqjDLksRY7-X',
    'WES_NSCLC_chr7': 	              '1OIWarGf6Q9SN9sUjtvH1jqjm4apj5q28', 
    'WES_NSCLC_chr7_bam': 	          '1uSJ0l9bKhX3E90WLRs9QRwyHo1Ljtsmp', 
    'RNAseq_PDAC_chr12':              '1RAVk6NxIyl-lyrwh0qoNu0Vm4R2V5ht9', 
    'RNAseq_PDAC_chr12_bam':          '1g0kBnw0s-6AuGieuW-O1-4pSsftk0sn9', 
    'RNAseq_NSCLC_chr7':              '1HF9N5USGkhxpjzsLmChAqtiIP4OuwelM', 
    'RNAseq_NSCLC_chr7_bam':          '1Ek2gTTGPPcaXqVee4XThcx7BgDgv9_5w', 
    'RNAseq_CRC_chr17': 	          '1KbV3o6r4pVPtlQur0xyiniJYS01DsPpM', 
    'RNAseq_CRC_chr17_bam':           '13FOOKwlMFgKJCg5-5x5gft0--zzHWAUc', 
    'RNAseq_CRC_chr17_gexp_results':  '1kJLU5AGuX4XmC1AbhX1kkn6F3A3jWtYD',
    'RNAseq_pacbio_chr7':             '1vIpKKmwpKz4XyRhCsUQ_CMQZrVOPNigZ',
    # 'RNAseq_pacbio_chr7_bam': '',
    'index_bwa_hg38_sel':             '1Ed9aMgOCmoFKYKj6-3WbEmQqepzRKUqJ',
    'index_star_hg38_sel':            '1VnU8oqEUPMViNX0QybywbW2jPY0Z1u4a',
    'index_rsem_hg38_sel':            '1Sy3DFcacd3sM3Fqi1egJhVfG4ZTWqD9i',
    'index_salmon_hg38_sel':          '1Q9yhzWuMdgHcNVUdNQGBjvTG307tzoD9'
    
}


def load_bi_workshop_data( item = None, file_type = 'tar.gz' ):

    tlst = list(bi_sample_data_fid_dict.keys())

    if item in tlst:
        file_id = bi_sample_data_fid_dict[item]
    else:
        print('The item must be one of .. \n   \'%s\' ' % ('\'\n   \''.join(tlst)))
        return None

    file_out = None
    try:
        file_down = download_from_google_drive( file_id )
        if file_type == 'tar.gz':
            file_out = decompress_tar_gz_folder( file_down, remove_org = True )
        elif file_type == 'zip':
            file_out = decompress_zip_folder(file_down, remove_zip=True)
            
    except:
        pass

    return file_out

'''
https://drive.google.com/file/d/1168GxVZMR466AQddsYwh-yiQ0nwamM9c/view?usp=sharing
https://drive.google.com/file/d/1hkyjJb51YoVlaO0lMXkoIx9kN-Tkjdce/view?usp=sharing
https://drive.google.com/file/d/1UYqTxjDElZuqJGwZtL8WSDAk-ow5dSGx/view?usp=sharing
https://drive.google.com/file/d/1wtAX4_kkyS-bxVGXEsnGFa9yGzCmiSHA/view?usp=sharing
https://drive.google.com/file/d/1xFRorHPAQI9oSNIPu3QscWIbsWCRpa1K/view?usp=sharing
'''

sers_data_fid_dict = {
    'SERS_lib':              '1168GxVZMR466AQddsYwh-yiQ0nwamM9c',
    'SERS_data_strawberry':  '1hkyjJb51YoVlaO0lMXkoIx9kN-Tkjdce',  
    'SERS_data_appletree':   '1UYqTxjDElZuqJGwZtL8WSDAk-ow5dSGx',    
    'Raw_data_strawberry': 	 '1wtAX4_kkyS-bxVGXEsnGFa9yGzCmiSHA',
    'Raw_data_appletree': 	 '1xFRorHPAQI9oSNIPu3QscWIbsWCRpa1K'
}


def load_sers_data( item = None, file_type = 'tar.gz', remove_downloaded = True ):

    tlst = list(sers_data_fid_dict.keys())

    if item in tlst:
        file_id = sers_data_fid_dict[item]
    else:
        print('The item must be one of .. \n   \'%s\' ' % ('\'\n   \''.join(tlst)))
        return None

    file_out = None
    try:
        file_down = download_from_google_drive( file_id )
        if file_type == 'tar.gz':
            file_out = decompress_tar_gz_folder( file_down, remove_org = remove_downloaded )
        elif file_type == 'zip':
            file_out = decompress_zip_folder(file_down, remove_zip = remove_downloaded)
            
    except:
        pass

    return file_out

