from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import fitz  # PyMuPDF
import json
import base64
import io

app = FastAPI()

@app.post("/crop")
async def crop_pdf(file: UploadFile = File(...), crops: str = Form(...)):
    try:
        # Ler o conteúdo do PDF enviado
        pdf_content = await file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        # Parse das coordenadas enviadas pelo Lovable/n8n
        crops_list = json.loads(crops)
        
        results = []
        for crop in crops_list:
            page_idx = int(crop['page']) - 1
            if page_idx >= len(doc):
                continue
                
            page = doc[page_idx]
            
            # Dimensões da página (points)
            p_w, p_h = page.rect.width, page.rect.height
            
            # Converte Percentual (0-1) -> Points
            x0 = float(crop['x']) * p_w
            y0 = float(crop['y']) * p_h
            x1 = (float(crop['x']) + float(crop['width'])) * p_w
            y1 = (float(crop['y']) + float(crop['height'])) * p_h
            
            # Recorte em Alta Resolução (Matrix 3 = 300% de zoom)
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(x0, y0, x1, y1))
            
            # Converter para Base64
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            
            results.append({
                "type": crop.get('type', 'unknown'),
                "page": crop['page'],
                "image_data": img_b64
            })
            
        doc.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)