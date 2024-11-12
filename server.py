from fastapi import FastAPI, Request, Response, File, UploadFile, BackgroundTasks
from fastapi.templating import Jinja2Templates
import ocr
import os
import shutil
import uuid
from models import Todo

app = FastAPI()
templates = Jinja2Templates(directories='templates')
todos = []

@app.get("/")
def home(request: Request):
    return templates.TemplatesResponse("index.html", {"request": request})

@app.post("/api/v1/extract_text")
async def extract_text(image: UploadFile = File(...)):
    temp_file = _save_file_to_disk(image, path='temp', save_as='temp')
    text = await ocr.read_image(temp_file)
    return {"filename": image.filename, "text": text}
    
@app.post("/api/v1/bulk_extract_text")
async def bulk_extract_text(request: Request, bg_task: BackgroundTasks):
    images = await request.form()
    folder_name = str(uuid.uuid4())
    os.mkdir(folder_name)
    
    for image in images.values():
        temp_file = _save_file_to_disk(image, path=folder_name, save_as=image.filename)  
     
    bg_task.add_task(ocr.read_image_form_dir, folder_name, write_to_file=True)
        
    return {"task_id": folder_name, "num_files": len(images)}

def _save_file_to_disk(uploaded_file, path=".", save_as='default'):
    extension = os.path.splitext(uploaded_file.filename)[-1]
    temp_file = os.path.join(path, save_as+extension)
    with open(temp_file, 'wb') as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer) 
    return temp_file

# Todo list
# Get all todos
@app.get("/todos")
async def get_todos():
    return {"Todos": todos}
     
# Get single todo
@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            return {"todo": todo}
    return {"message": "No todo found!"}
    
# Create a new todo
@app.post("/todos")
async def create_todo(todo: Todo):
    todos.append(todo)
    return {"message": "Todo has been added."}
    
# Delete a single todo
@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            todos.remove(todo)
            return {"message": "Todo has been DELETED."}
    return {"message": "No todo found!"}
# Update a single todo
@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, todo_obj: Todo):
    for todo in todos:
        if todo.id == todo_id:
            todo.id = todo_id
            todo.item = todo_obj.item
            return {"todo": todo}
    return {"message": "Todo has been UPDATED."}
    