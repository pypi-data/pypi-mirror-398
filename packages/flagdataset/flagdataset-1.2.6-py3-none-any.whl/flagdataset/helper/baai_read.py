import psutil
import csv


from .baai_jwtsign import jwtsign_parse

def read_local_meta(bin_path):
    with open(bin_path, 'r') as freader:
        csv_reader = csv.DictReader(freader)
        csv_list = list(csv_reader)

    for row in csv_list:
        try:
            sign_data = jwtsign_parse(row["download_sign"])
            download_size = psutil._common.bytes2human(int(row["download_size"]))
            # yield f"{sign_data["proto"]} {sign_data["prefix"]} {sign_data["path"]}", download_size
            yield f"{sign_data['path']}", download_size
        except Exception as e:
            print(e)



def read_base_meta(bin_path):
    with open(bin_path, 'r') as freader:
        csv_reader = csv.DictReader(freader)
        csv_list = list(csv_reader)

    for row in csv_list:
        try:
            yield row["download_sign"], int(row["download_size"]), row["download_extn"]
        except Exception as e:
            print(e)