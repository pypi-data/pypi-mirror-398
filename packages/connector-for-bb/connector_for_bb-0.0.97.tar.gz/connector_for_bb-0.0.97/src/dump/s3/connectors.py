import logging
import os
import warnings
from typing import Dict, Optional

import boto3
import pandas as pd
from botocore.config import Config
from pandas import DataFrame as PandasDataFrame

from dump.config_utils import load_config
from dump.files.tmp_util import TemporaryFileSystem


ZIP_FORMATS_DICT = {"zip": "zip", "orc": "orc", "gz": "gzip"}


class S3Client:
    def __init__(
        self, creds_section: str, config_filiname: str = "s3_config.ini"
    ) -> None:
        self.creds_section = creds_section

        self.config = load_config(filename=config_filiname, section=creds_section)
        self.conn_config = Config(
            s3={
                "addressing_style": "virtual",
            },
            retries={"max_attempts": 10, "mode": "standard"},
            region_name="us-east-1",
        )

        self.client = boto3.client(
            "s3",
            **self.config,
            config=self.conn_config,
        )

    def get_files_info(self, bucket_name: str, object_folder: Optional[str] = ""):
        files_dict = {}
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=object_folder)
        for response in pages:
            if "Contents" in response:
                for obj in response["Contents"]:
                    size = obj["Size"]
                    files_dict[obj["Key"]] = {
                        "size_bytes": size,
                        "size_gb": size / 1024**3,
                    }
        return files_dict


class S3Upload(S3Client):
    """
    To upload files to s3
    """

    def __init__(
        self,
        bucket_name: str,
        object_folder: str = "",
        creds_section: str = "test",
    ) -> None:
        super().__init__(creds_section)
        self.bucket_name = bucket_name
        self.object_folder = object_folder

    def _get_path(self, file_name: str) -> str:
        """
        creating path where to save file in s3
        """
        path = os.path.join(self.object_folder, file_name)
        return path

    def upload_to_s3(self, tmp_path_file: str, file_name: str):
        """
        tmp_path_file: str - file location that we want to save
        file_name: str - new file name that will be displayed in s3

        upload local file into s3 bucket with new name 'file_name'
        """
        path = self._get_path(file_name)
        self.client.upload_file(tmp_path_file, self.bucket_name, path)


class S3UploadDF(S3Upload):
    def __init__(
        self,
        df_compression=False,
        df_compression_format: str = "gz",
        orc_compession_engine: str = "ZLIB",
        compresslevel: int = 4,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.df_compression = df_compression
        self.df_compression_format = df_compression_format
        self.orc_compession_engine = orc_compession_engine
        self.compresslevel = compresslevel

        if self.df_compression:
            if self.df_compression_format not in ZIP_FORMATS_DICT.keys():
                raise ValueError(
                    f"Unkowm df_compression_format: {self.df_compression_format}, avaliable formats: {ZIP_FORMATS_DICT.keys()}"
                )
            if self.df_compression_format == "orc":
                tmp_file_format = f"orc"
            else:
                tmp_file_format = f"csv.{self.df_compression_format}"

            self._tmp_file_system = TemporaryFileSystem(file_format=tmp_file_format)
        else:
            self._tmp_file_system = TemporaryFileSystem(file_format="csv")

    def __del__(self):
        self._tmp_file_system.cleanup()

    def __get_file_name_no_ext(self, file_name: str):
        splited_file = file_name.split(".")
        extension = splited_file[-1]

        if extension in ZIP_FORMATS_DICT:
            logging.info(
                "In filename already specified extension, that will be ignored."
            )

        return splited_file[0]

    def upload_to_s3_df(self, df: PandasDataFrame, file_name: str):
        save_path = self._tmp_file_system.save_path()
        file_extension = file_name.split(".")[-1]

        if not self.df_compression:
            # if  doesnt need compression
            if file_extension in ZIP_FORMATS_DICT:
                raise ValueError(
                    f"You pass filename contains: '{file_extension}' format in it. U should pass df_compression=True"
                )
            df.to_csv(save_path, index=False)
        elif self.df_compression_format != "orc":
            file_name_no_ext = self.__get_file_name_no_ext(file_name)
            file_name = f"{file_name_no_ext}.csv.{self.df_compression_format}"

            compression_opts = dict(
                method=ZIP_FORMATS_DICT.get(self.df_compression_format),
                compresslevel=self.compresslevel,
            )
            df.to_csv(save_path, index=False, compression=compression_opts)
        elif self.df_compression_format == "orc":
            file_name_no_ext = self.__get_file_name_no_ext(file_name)
            file_name = f"{file_name_no_ext}.{self.df_compression_format}"

            compression_opts = dict(compression=self.orc_compession_engine)
            df.to_orc(save_path, engine_kwargs=compression_opts)

        logging.info(f"uploading to s3, path: {save_path}")
        logging.info(f"uploading to s3, filename: {file_name}")
        self.upload_to_s3(save_path, file_name)


class S3Download(S3Client):
    def __init__(
        self,
        bucket_name: str,
        object_folder: str = "",
        creds_section: str = "test",
    ) -> None:
        super().__init__(creds_section)
        self.bucket_name = bucket_name
        self.object_folder = object_folder

        self._tmp_file_system = TemporaryFileSystem()

        # requires for not download same file more than one time
        self.__downloads_history: Dict[str, str] = {}

    def __del__(self):
        self._tmp_file_system.cleanup()

    def _check_path_exist(self, path: str) -> bool:
        exsist_files = self.get_files_info(self.bucket_name, self.object_folder)
        return path in exsist_files

    def _get_object_path(self, file_name) -> str:
        path = os.path.join(self.object_folder, file_name)
        return path

    def __validate_file_system_by_filename(self, download_file_name: str):
        extension = download_file_name.split(".")[-1]
        if extension:
            self._tmp_file_system.file_format = extension

    def download_from_s3(self, download_file_name: str) -> str:
        """
        downloading file from s3 and put the file into temporary directory
        returns path to file in temporary directory
        """
        self.__validate_file_system_by_filename(download_file_name)

        object_path = self._get_object_path(download_file_name)
        if self._check_path_exist(object_path):
            if object_path not in self.__downloads_history:
                save_path = self._tmp_file_system.save_path()
                self.client.download_file(self.bucket_name, object_path, save_path)
                self.__downloads_history[object_path] = save_path

            return self.__downloads_history[object_path]
        else:
            raise ValueError(f"The file {object_path} was not found")

    def download_from_s3_df(
        self, download_file_name: str, encoding="utf-8"
    ) -> PandasDataFrame:
        if download_file_name.split(".")[-1] == "orc":
            warnings.warn("Next time use download_from_s3_df_orc method!")
            return self.download_from_s3_df_orc(download_file_name)

        df_path = self.download_from_s3(download_file_name)
        return pd.read_csv(df_path, encoding=encoding, low_memory=False)

    def download_from_s3_df_orc(self, download_file_name: str) -> PandasDataFrame:
        df_path = self.download_from_s3(download_file_name)
        return pd.read_orc(df_path)
