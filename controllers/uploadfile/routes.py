# backend/tancho/pets/routes.py
import shutil
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable
from bson.objectid import ObjectId
from config.config import DB, CONF
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse
from typing import List
import logging
from fastapi.responses import FileResponse

uploadfile_router = APIRouter()


def validate_object_id(id_: str):
    try:
        _id = ObjectId(id_)
    except Exception:
        if CONF["fastapi"].get("debug", False):
            logging.warning("Invalid Object ID")
        raise HTTPException(status_code=400)
    return _id


async def _get_user_or_404(id_: str):
    _id = validate_object_id(id_)
    pet = await DB.users.find_one({"_id": _id})
    if pet:
        return fix_pet_id(pet)
    else:
        raise HTTPException(status_code=404, detail="Pet not found")


def fix_pet_id(id):
    id["id_"] = str(id["_id"])
    return id

async def add_registro(registro):
    """[summary]
    Inserts a new user on the DB.

    [description]
    Endpoint to add a new user.
    """
    try:
        conteo = DB.myfiles.find({}, {'registro': 1}).sort('registro', -1).limit(1)
        conteo = await conteo.to_list(length=1)
        registro = registro.dict()
        registro['registro'] = conteo[0]['registro'] + 1
    except:
        registro['registro'] = 0
    registro_op = await DB.proveedor.insert_one(registro)
    return {
        "id": str(registro_op.inserted_id),
        "registro": registro['registro']
    }

@uploadfile_router.get("/getfile/{filename}")
async def main(filename):
    return FileResponse("fileserver/{}".format(filename))
    # return FileResponse("hola.jpg")


@uploadfile_router.post("/files/")
async def create_files(files: List[bytes] = File(...)):
    print(files)
    global upload_folder
    upload_folder = 'fileserver'
    file_object = files
    # create empty file to copy the file_object to
    upload_folder = open(os.path.join(upload_folder, "nuevo.jpg"), 'wb+')
    shutil.copyfileobj(file_object, upload_folder)
    upload_folder.close()
    return {"filename": "nuevo.jpg"}
    # return {"file_sizes": [len(file) for file in files]}


@uploadfile_router.post("/upload")
def create_file(file: UploadFile = File(...)):
    print("file", file)
    global upload_folder
    upload_folder = 'fileserver'
    file_object = file.file
    # create empty file to copy the file_object to
    upload_folder = open(os.path.join(upload_folder, file.filename), 'wb+')
    shutil.copyfileobj(file_object, upload_folder)
    upload_folder.close()
    return {"filename": file.filename}


@uploadfile_router.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    print(files[0].filename)
    global upload_folder
    upload_folder = 'fileserver'
    file_object = files[0].file
    upload_folder = open(os.path.join(upload_folder, files[0].filename), 'wb+')
    shutil.copyfileobj(file_object, upload_folder)
    upload_folder.close()
    return {"filenames": [file.filename for file in files]}


@uploadfile_router.get("/")
async def main():
    content = """
<body>
<form action="/fileserver/myfiles/files/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
<form action="/fileserver/myfiles/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)
