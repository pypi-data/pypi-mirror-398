# Guía de Publicación en PyPI

Guía completa para publicar **Flash-Fuzzy Python** en PyPI usando Maturin.

## Requisitos Previos

- ✅ Python 3.8+ instalado
- ✅ Rust toolchain instalado
- ⏳ Cuenta en PyPI (https://pypi.org)
- ⏳ Maturin instalado

## Paso 1: Crear Cuenta en PyPI

1. Ve a https://pypi.org/account/register/
2. Completa el formulario de registro
3. Verifica tu email
4. **Habilita 2FA** (Two-Factor Authentication) - REQUERIDO para publicar

### Configurar 2FA

1. Ve a https://pypi.org/manage/account/
2. Click en "Add 2FA with authentication application"
3. Escanea el QR con una app como Google Authenticator o Authy
4. Guarda los códigos de recuperación en un lugar seguro

## Paso 2: Crear API Token

PyPI ya no acepta passwords para publicar, debes usar API tokens:

1. Ve a https://pypi.org/manage/account/token/
2. Click en "Add API token"
3. **Token name**: `flash-fuzzy-publish`
4. **Scope**:
   - Inicialmente: "Entire account" (para primera publicación)
   - Después: "Project: flash-fuzzy" (más seguro)
5. Click en "Add token"
6. **COPIA EL TOKEN INMEDIATAMENTE** (solo se muestra una vez)
   - Formato: `pypi-AgEIcHlwaS5vcmc...` (muy largo)

**Guarda el token** en un lugar seguro (password manager).

## Paso 3: Instalar Maturin

Maturin es la herramienta para construir y publicar paquetes Rust-Python.

```bash
# Instalar maturin
pip install maturin

# Verificar instalación
maturin --version
```

## Paso 4: Configurar Credenciales

### Opción A: Variable de Entorno (Recomendado para CI/CD)

```bash
# Windows (PowerShell)
$env:MATURIN_PYPI_TOKEN = "pypi-AgEIcHlwaS5vcmc..."

# Linux/Mac
export MATURIN_PYPI_TOKEN="pypi-AgEIcHlwaS5vcmc..."
```

### Opción B: Archivo .pypirc (Local)

Crea/edita `~/.pypirc` (Windows: `C:\Users\TuUsuario\.pypirc`):

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
```

**Seguridad**: Asegúrate de que este archivo solo sea legible por ti:

```bash
# Linux/Mac
chmod 600 ~/.pypirc
```

## Paso 5: Construir el Paquete

Desde el directorio `FlashFuzzy/bindings/python/`:

### 5.1: Construir Localmente (Testing)

```bash
cd FlashFuzzy/bindings/python

# Build para tu plataforma actual
maturin build --release

# El wheel se guarda en: target/wheels/
# Ejemplo: flash_fuzzy-0.1.0-cp312-cp312-win_amd64.whl
```

### 5.2: Probar el Build Localmente

```bash
# Crear entorno virtual
python -m venv venv

# Activar
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar el wheel
pip install target/wheels/flash_fuzzy-0.1.0-*.whl

# Probar
python -c "from flash_fuzzy import FlashFuzzy; print('OK!')"
```

## Paso 6: Publicar en PyPI

### 6.1: Publicación con Maturin (Recomendado)

Maturin puede construir wheels para múltiples plataformas y publicar automáticamente:

```bash
cd FlashFuzzy/bindings/python

# Publicar (construye para tu plataforma y publica)
maturin publish --username __token__ --password $MATURIN_PYPI_TOKEN
```

O si configuraste `.pypirc`:

```bash
maturin publish
```

### 6.2: Construcción Multiplataforma (GitHub Actions)

Para dar soporte a todas las plataformas, usa GitHub Actions. Maturin tiene una action oficial:

Crea `.github/workflows/publish-python.yml`:

```yaml
name: Publish Python Package

on:
  release:
    types: [created]

jobs:
  build-wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Build wheels
        uses: PyO3/maturin-action@v1
        with:
          command: build
          args: --release --out dist
          working-directory: bindings/python

      - uses: actions/upload-artifact@v3
        with:
          name: wheels
          path: bindings/python/dist

  publish:
    needs: [build-wheels]
    runs-on: ubuntu-latest

    steps:
      - uses: actions/download-artifact@v3
        with:
          name: wheels
          path: dist

      - uses: PyO3/maturin-action@v1
        with:
          command: upload
          args: --skip-existing dist/*
        env:
          MATURIN_PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

**Configurar Secret en GitHub:**
1. Ve a tu repositorio > Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Name: `PYPI_TOKEN`
4. Value: Tu token de PyPI
5. Click "Add secret"

## Paso 7: Verificar Publicación

1. **PyPI**: https://pypi.org/project/flash-fuzzy/
2. **Instalar desde PyPI**:
   ```bash
   pip install flash-fuzzy
   ```

3. **Verificar que funciona**:
   ```python
   from flash_fuzzy import FlashFuzzy
   ff = FlashFuzzy()
   ff.add({"id": 1, "text": "test"})
   results = ff.search("test")
   print(results)
   ```

## Paso 8: Publicar Nueva Versión

1. **Actualizar versión** en `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. **Actualizar versión** en `python/flash_fuzzy/__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```

3. **Crear tag en Git**:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

4. **Publicar**:
   ```bash
   maturin publish
   ```

## Troubleshooting

### Error: "Invalid username/password"

**Solución**: Verifica que uses `__token__` como username (con doble underscore) y el token completo como password.

### Error: "File already exists"

**Solución**: No puedes sobrescribir una versión ya publicada. Incrementa la versión en `pyproject.toml`.

### Error: "Missing required metadata"

**Solución**: Verifica que `pyproject.toml` tenga todos los campos requeridos:
- name, version, description, authors, license

### Error: "Rust compiler not found"

**Solución**: Instala Rust:
```bash
# Windows
https://rustup.rs/

# Linux/Mac
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Build falla en Windows

**Solución**: Instala Visual Studio Build Tools:
- https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Selecciona "Desktop development with C++"

### ImportError al importar el módulo

**Solución**: Verifica que la extensión se compiló para la versión correcta de Python:
```bash
python --version  # Debe coincidir con cpXXX en el nombre del wheel
```

## Comandos Útiles

### Construir para testing

```bash
# Build en modo debug (más rápido)
maturin develop

# Build y instala en el venv actual
maturin develop --release
```

### Construir wheels sin publicar

```bash
# Solo construir
maturin build --release

# Construir para múltiples versiones de Python
maturin build --release --interpreter python3.8 python3.9 python3.10
```

### Publicar en TestPyPI (Testing)

```bash
# Registrarse en https://test.pypi.org
# Crear token en TestPyPI

# Publicar
maturin publish --repository testpypi --username __token__ --password $TESTPYPI_TOKEN

# Instalar desde TestPyPI
pip install --index-url https://test.pypi.org/simple/ flash-fuzzy
```

## Checklist de Publicación

Antes de publicar, verifica:

- [ ] Cuenta PyPI creada y 2FA habilitado
- [ ] API Token creado y guardado
- [ ] Maturin instalado (`maturin --version`)
- [ ] pyproject.toml actualizado con versión correcta
- [ ] `__version__` actualizado en `__init__.py`
- [ ] README.md actualizado
- [ ] Tests pasan: `pytest tests/`
- [ ] Build local exitoso: `maturin build --release`
- [ ] Código commiteado y pusheado a Git
- [ ] Tag de versión creado

## Estructura de Archivos

```
FlashFuzzy/bindings/python/
├── pyproject.toml          # Metadata del paquete
├── Cargo.toml              # Configuración Rust
├── README.md               # Documentación
├── src/                    # Código Rust (PyO3)
│   └── lib.rs
├── python/flash_fuzzy/     # Código Python wrapper
│   └── __init__.py
└── tests/                  # Tests
    └── test_basic.py
```

## Recursos Adicionales

- **Maturin Docs**: https://www.maturin.rs/
- **PyO3 Guide**: https://pyo3.rs/
- **PyPI Packaging Guide**: https://packaging.python.org/
- **Python Wheels**: https://pythonwheels.com/

## Soporte

Si tienes problemas durante la publicación:

1. Revisa los logs de error
2. Consulta la documentación de Maturin
3. Abre un issue en GitHub: https://github.com/RafaCalRob/FlashFuzzy/issues
