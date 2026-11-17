import hashlib
import hmac
import json
import os

CARPETA_DATOS = "data"
ARCHIVO_CREDENCIALES = "data/credenciales.json"
ITERACIONES = 200_000


def generar_hash(contrasena: str, sal: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode("utf-8"), sal, ITERACIONES
    ).hex()


def comprobar_contrasena(contrasena: str, sal: bytes, hash_guardado: str) -> bool:
    return hmac.compare_digest(generar_hash(contrasena, sal), hash_guardado)


def existe_contrasena() -> bool:
    return os.path.exists(ARCHIVO_CREDENCIALES)


def guardar_contrasena(contrasena: str) -> None:
    sal = os.urandom(16)
    credenciales = {"sal": sal.hex(), "hash": generar_hash(contrasena, sal)}
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    with open(ARCHIVO_CREDENCIALES, "w", encoding="utf-8") as archivo:
        json.dump(credenciales, archivo)


def verificar_contrasena(contrasena: str) -> bool:
    with open(ARCHIVO_CREDENCIALES, encoding="utf-8") as archivo:
        credenciales = json.load(archivo)
    sal = bytes.fromhex(credenciales["sal"])
    return comprobar_contrasena(contrasena, sal, credenciales["hash"])
