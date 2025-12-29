FORMDATA_TEMPLATE = """\
from datetime import datetime
import os
import shutil
from typing import Any, List, Type, Union
from fastapi import Form, UploadFile
from fastapi.responses import FileResponse
from .utils import ResponseUtils

AppUtils = ResponseUtils


class FormDataAccess:
    BASE_UPLOAD_DIR = "uploads"

    @staticmethod
    def parse_list(model: Type[Any]):
        def _parser(items: List[str] = Form(...)):
            return [model.parse_raw(item) for item in items]

        return _parser

    @staticmethod
    def _ensure_folder(folder_name: str):
        
        folder_path = os.path.join(FormDataAccess.BASE_UPLOAD_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    # -------------------------------
    # File Upload
    # -------------------------------
    @staticmethod
    async def uploadFiles(folder_name: str, files: Union[UploadFile, List[UploadFile]]):
        try:
            if not isinstance(files, list):
                files = [files]
            folder_path = FormDataAccess._ensure_folder(folder_name)
            saved_files = []

            for file in files:
                current_dt = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(file.filename)
                new_filename = f"{name}_{current_dt}{ext}"
                file_path = os.path.join(folder_path, new_filename)

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                saved_files.append({"filename": new_filename, "filepath": file_path})

            return saved_files
        except Exception as ex:
            raise ex

    # -------------------------------
    # File Download
    # -------------------------------
    @staticmethod
    def downloadFiles(folder_name: str, filenames: Union[str, List[str]]):
        try:
            if isinstance(filenames, str):
                filenames = [filenames]

            folder_path = FormDataAccess._ensure_folder(folder_name)
            file_responses = []

            for fname in filenames:
                file_path = os.path.join(folder_path, fname)
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File {fname} not found")
                file_responses.append(FileResponse(file_path, filename=fname))

            if len(file_responses) == 1:
                return file_responses[0]
            else:
                zip_path = os.path.join(folder_path, "downloaded_files.zip")
                shutil.make_archive(zip_path.replace(".zip", ""), "zip", folder_path)
                return FileResponse(zip_path, filename="downloaded_files.zip")

        except Exception as ex:
            raise ex

    @staticmethod
    def removeFiles(folder_name: str, filenames: Union[str, List[str]]):
        try:
            if isinstance(filenames, str):
                filenames = [filenames]

            folder_path = FormDataAccess._ensure_folder(folder_name)
            removed_files = []
            not_found = []

            for fname in filenames:
                # ✅ Auto handle full path input
                fname = os.path.basename(fname)

                file_path = os.path.join(folder_path, fname)

                if os.path.exists(file_path):
                    os.remove(file_path)
                    removed_files.append(fname)
                else:
                    not_found.append(fname)

            return AppUtils.responseWithData(
                True,
                200,
                "File delete process completed",
                {"deleted": removed_files, "not_found": not_found},
            )
        except Exception as ex:
            raise ex

"""
