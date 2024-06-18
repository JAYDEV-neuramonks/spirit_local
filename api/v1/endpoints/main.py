from app.clients.spirit.invoice_app import invoice_functions
from app.clients.spirit.config import settings
import os
output_dir = os.path.join(settings.working_dir , 'output')
input_dir = os.path.join(settings.working_dir, 'input')
    
from fastapi import FastAPI, HTTPException, Request
import json

app = FastAPI()



@app.get("/test")
async def status():
    return {"message": "Spirit GenAPI v1"}

   

@app.post("/analyze_invoice")
async def analyze_invoice(request: Request):
    try:
        invoice_data = await request.json()
        response = invoice_functions.process_json_file(invoice_data, input_dir, output_dir)    
        print(response)
        if response ["sentence"]:
            del response ["sentence"] 
        return {"message": response}
    except Exception as e:
        print(f"Error processing invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#this version  use the data model, which is not available at the moment
'''
@app.post("/analyze_invoice_strict")
async def analyze_invoice(invoice_data: RootModel):
    try:
        print("Received invoice data>>")
        print("Received invoice data:", invoice_data.dict())
        return
        response = invoice_functions.process_json_files(input_dir, output_dir)
                
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

'''

@app.get("/get_analyze_invoice")
async def analyze_invoice():
    try:
        response = invoice_functions.process_json_files(input_dir, output_dir)                
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))