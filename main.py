from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import subprocess


app = FastAPI()
templates = Jinja2Templates(directory="html")

CONFIG_FILE_PATH = "/srv/ansible/amenet/create_conf/"
CONFIG_FILE_PATH_2 = "/srv/ansible/amenet/create_conf/output.txt"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/config-generator", response_class=HTMLResponse)
async def config_generator(request: Request):
    return templates.TemplateResponse("config_form.html", {"request": request})


@app.post("/generate-config")
async def generate_config(
        ip: str = Form(...),
        subnet: str = Form(...),
        vlan_mng: str = Form(...),
        gate: str = Form(...),
        hostname: str = Form(...),
        location: str = Form(...)
):
    # Передача данных в Ansible плейбук
    extra_vars = {
        "ip": ip,
        "subnet": subnet,
        "vlan_mng": vlan_mng,
        "gate": gate,
        "hostname": hostname,
        "location": location
    }

    try:
        # Выполнение Ansible плейбука
        result = subprocess.run(
            [
                "ansible-playbook",
                "create_conf.yml",
                "-e", f"ip={ip} subnet={subnet} vlan_mng={vlan_mng} gate={gate} hostname={hostname} location={location}"
            ],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:  # Проверка успешного выполнения
            # Проверяем, существует ли файл
            if os.path.exists(CONFIG_FILE_PATH_2):
                # Перенаправляем пользователя на страницу с действиями
                return RedirectResponse(url="/config-actions", status_code=303)
            else:
                return {"status": "error", "message": "Файл не был создан."}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/config-actions", response_class=HTMLResponse)
async def config_actions(request: Request):
    # Возвращаем страницу с кнопками "Показать конфиг" и "Скачать конфиг"
    return templates.TemplateResponse("config_actions.html", {"request": request})

@app.get("/view-config", response_class=PlainTextResponse)
async def view_config():
    # Читаем содержимое файла и отображаем его в браузере
    if os.path.exists(CONFIG_FILE_PATH_2):
        with open(CONFIG_FILE_PATH_2, "r") as file:
            content = file.read()
        return PlainTextResponse(content)
    else:
        return {"status": "error", "message": "Файл не найден."}


@app.get("/download-config", response_class=FileResponse)
async def download_config():
    # Отправляем файл клиенту для скачивания
    if os.path.exists(CONFIG_FILE_PATH_2):
        return FileResponse(
            path=CONFIG_FILE_PATH_2,
            filename="output.txt",
            media_type="text/plain"
        )
    else:
        return {"status": "error", "message": "Файл не найден."}