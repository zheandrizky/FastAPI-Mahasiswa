# from typing import Union
# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def read_root():

#     return {"Hello": "World"}

# conda activate webservicep2plending webservicep2plending
# uvicorn main:app --reload


from typing import Union
from fastapi import FastAPI,Response,Request,HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/mahasiswa/{nim}")
def ambil_mhs(nim:str):
    return {"nama": "Budi Martami"}

@app.get("/mahasiswa2/")
def ambil_mhs2(nim:str):
    return {"nama": "Budi Martami 2"}

@app.get("/daftar_mhs/")
def daftar_mhs(id_prov:str,angkatan:str):
    return {"query":" idprov: {}  ; angkatan: {} ".format(id_prov,angkatan),"data":[{"nim":"1234"},{"nim":"1235"}]}

# panggil sekali saja
@app.get("/init/")
def init_db():
  try:
    DB_NAME = "upi.db"
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    create_table = """ CREATE TABLE mahasiswa(
            ID      	INTEGER PRIMARY KEY 	AUTOINCREMENT,
            nim     	TEXT            	NOT NULL,
            nama    	TEXT            	NOT NULL,
            id_prov 	TEXT            	NOT NULL,
            angkatan	TEXT            	NOT NULL,
            tinggi_badan  INTEGER
        )  
        """
    cur.execute(create_table)
    con.commit
  except:
           return ({"status":"terjadi error"})  
  finally:
           con.close()
    
  return ({"status":"ok, db dan tabel berhasil dicreate"})

from pydantic import BaseModel

from typing import Optional

class Mhs(BaseModel):
   nim: str
   nama: str
   id_prov: str
   angkatan: str
   tinggi_badan: Optional[int] | None = None  # yang boleh null hanya ini


#status code 201 standard return creation
#return objek yang baru dicreate (response_model tipenya Mhs)
@app.post("/tambah_mhs/", response_model=Mhs,status_code=201)  
def tambah_mhs(m: Mhs,response: Response, request: Request):
   try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       # hanya untuk test, rawal sql injecttion, gunakan spt SQLAlchemy
       cur.execute("""insert into mahasiswa (nim,nama,id_prov,angkatan,tinggi_badan) values ( "{}","{}","{}","{}",{})""".format(m.nim,m.nama,m.id_prov,m.angkatan,m.tinggi_badan))
       con.commit() 
   except:
       print("oioi error")
       return ({"status":"terjadi error"})   
   finally:  	 
       con.close()
   response.headers["Location"] = "/mahasiswa/{}".format(m.nim) 
   print(m.nim)
   print(m.nama)
   print(m.angkatan)
  
   return m



@app.get("/tampilkan_semua_mhs/")
def tampil_semua_mhs():
   try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       recs = []
       for row in cur.execute("select * from mahasiswa"):
           recs.append(row)
   except:
       return ({"status":"terjadi error"})   
   finally:  	 
       con.close()
   return {"data":recs}

from fastapi.encoders import jsonable_encoder


@app.put("/update_mhs_put/{nim}",response_model=Mhs)
def update_mhs_put(response: Response,nim: str, m: Mhs ):
    #update keseluruhan
    #karena key, nim tidak diupdape
    try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       cur.execute("select * from mahasiswa where nim = ?", (nim,) )  #tambah koma untuk menandakan tupple
       existing_item = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))   
    
    if existing_item:  #data ada 
            print(m.tinggi_badan)
            cur.execute("update mahasiswa set nama = ?, id_prov = ?, angkatan=?, tinggi_badan=? where nim=?", (m.nama,m.id_prov,m.angkatan,m.tinggi_badan,nim))
            con.commit()            
            response.headers["location"] = "/mahasiswa/{}".format(m.nim)
    else:  # data tidak ada
            print("item not foud")
            raise HTTPException(status_code=404, detail="Item Not Found")
      
    con.close()
    return m


# khusus untuk patch, jadi boleh tidak ada
# menggunakan "kosong" dan -9999 supaya bisa membedakan apakah tdk diupdate ("kosong") atau mau
# diupdate dengan dengan None atau 0
class MhsPatch(BaseModel):
   nama: str | None = "kosong"
   id_prov: str | None = "kosong"
   angkatan: str | None = "kosong"
   tinggi_badan: Optional[int] | None = -9999  # yang boleh null hanya ini



@app.patch("/update_mhs_patch/{nim}",response_model = MhsPatch)
def update_mhs_patch(response: Response, nim: str, m: MhsPatch ):
    try:
      print(str(m))
      DB_NAME = "upi.db"
      con = sqlite3.connect(DB_NAME)
      cur = con.cursor() 
      cur.execute("select * from mahasiswa where nim = ?", (nim,) )  #tambah koma untuk menandakan tupple
      existing_item = cur.fetchone()
    except Exception as e:
      raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e))) # misal database down  
    
    if existing_item:  #data ada, lakukan update
        sqlstr = "update mahasiswa set " #asumsi minimal ada satu field update
        # todo: bisa direfaktor dan dirapikan
        if m.nama!="kosong":
            if m.nama!=None:
                sqlstr = sqlstr + " nama = '{}' ,".format(m.nama)
            else:     
                sqlstr = sqlstr + " nama = null ,"
        
        if m.angkatan!="kosong":
            if m.angkatan!=None:
                sqlstr = sqlstr + " angkatan = '{}' ,".format(m.angkatan)
            else:
                sqlstr = sqlstr + " angkatan = null ,"
        
        if m.id_prov!="kosong":
            if m.id_prov!=None:
                sqlstr = sqlstr + " id_prov = '{}' ,".format(m.id_prov) 
            else:
                sqlstr = sqlstr + " id_prov = null, "     

        if m.tinggi_badan!=-9999:
            if m.tinggi_badan!=None:
                sqlstr = sqlstr + " tinggi_badan = {} ,".format(m.tinggi_badan)
            else:    
                sqlstr = sqlstr + " tinggi_badan = null ,"

        sqlstr = sqlstr[:-1] + " where nim='{}' ".format(nim)  #buang koma yang trakhir  
        print(sqlstr)      
        try:
            cur.execute(sqlstr)
            con.commit()         
            response.headers["location"] = "/mahasixswa/{}".format(nim)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))   
        

    else:  # data tidak ada 404, item not found
         raise HTTPException(status_code=404, detail="Item Not Found")
   
    con.close()
    return m
  
    
@app.delete("/delete_mhs/{nim}")
def delete_mhs(nim: str):
    try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       sqlstr = "delete from mahasiswa  where nim='{}'".format(nim)                 
       print(sqlstr) # debug 
       cur.execute(sqlstr)
       con.commit()
    except:
       return ({"status":"terjadi error"})   
    finally:  	 
       con.close()
    
    return {"status":"ok"}


from fastapi import File, UploadFile
from fastapi.responses import FileResponse

# upload image
@app.post("/uploadimage")
def upload(file: UploadFile = File(...)):
    try:
        print("mulai upload")
        print(file.filename)
        contents = file.file.read()
        with open("./data_file/"+file.filename, 'wb') as f:
            f.write(contents)
    except Exception:
        return {"message": "Error upload file"}
    finally:
        file.file.close()
    return {"message": f"Upload berhasil: {file.filename}"}

# ambil image berdasarkan nama file
@app.get("/getimage/{nama_file}")
async def getImage(nama_file: str):
    return FileResponse("./data_file/"+nama_file)
