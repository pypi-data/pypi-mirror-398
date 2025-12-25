<h1 align="center">
  <a href="https://www.statamcp.com">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="logo" width="300"/>
  </a>
</h1>

<h1 align="center">Stata-MCP</h1>

<p align="center"> Deja que LLM te ayude a realizar tu análisis de regresión con Stata. ✨</p>

[![en](https://img.shields.io/badge/lang-English-red.svg)](../../../../README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](../cn/README.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](../fr/README.md)
[![sp](https://img.shields.io/badge/Idioma-Español-green.svg)](README.md)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](../../../../LICENSE)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/stata-mcp/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/stata-mcp)

---
**Nota:** Después del lanzamiento de la v2.0.0, este documento ya no se actualizará. Para más contenido, consulte el README en inglés [aquí](../../../../README.md).

Novedad: Ahora puedes usar Stata-MCP en modo agente, más información [aquí](../../../agent_examples/README.md).


> ¿Buscando otros?
>
> - [Trace DID](https://github.com/asjadnaqvi/DiD): Si quieres obtener la información más reciente sobre DID (Difference-in-Difference), haz clic [aquí](https://asjadnaqvi.github.io/DiD/). Ahora hay una traducción española por [Sepine Tam](https://github.com/sepine) y [StataMCP-Team](https://github.com/statamcp-team) 🎉
> - Uso en Jupyter Lab (Importante: Stata 17+) [aquí](../../JupyterStata.md)
> - [NBER-MCP](https://github.com/sepinetam/NBER-MCP) & [AER-MCP](https://github.com/sepinetam/AER-MCP) 🔧 en construcción
> - [Econometrics-Agent](https://github.com/FromCSUZhou/Econometrics-Agent)
> - [TexIV](https://github.com/sepinetam/TexIV): Un marco impulsado por aprendizaje automático que transforma datos de texto en variables utilizables para investigación empírica utilizando técnicas avanzadas de NLP y ML
> - Una integración para VScode o Cursor [aquí](https://github.com/hanlulong/stata-mcp). ¿Confundido? 💡 [Diferencias](../../Difference.md)

## 💡 Inicio Rápido
### Modo Agente
Los detalles del modo agente se encuentran [aquí](../../../agent_examples/README.md).

```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv sync
uv pip install -e .

stata-mcp --version  # para probar si stata-mcp está instalado correctamente.
stata-mcp --agent  # ahora puedes disfrutar del modo agente stata-mcp.
```

o puedes usarlo directamente con `uvx`:
```bash
uvx stata-mcp --version  # para probar si se puede usar en su computadora.
uvx stata-mcp --agent
```

### Modo Cliente Chat-Bot IA
> La configuración estándar requiere que Stata esté instalado en la ruta predeterminada y que exista la interfaz de línea de comandos de Stata (para macOS y Linux).

El archivo json de configuración estándar es el siguiente; puedes personalizar tu configuración añadiendo variables de entorno.
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

Para información más detallada sobre el uso, visita la [guía de Uso](../../Usages/Usage.md).

Y para un uso más avanzado, visita la [Guía avanzada](../../Usages/Advanced.md)

### Requisitos previos
- [uv](https://github.com/astral-sh/uv) - Instalador de paquetes y gestor de entornos virtuales
- Claude, Cline, ChatWise u otro servicio LLM
- Licencia de Stata
- Tu API-KEY del LLM

> Notas:
> 1. Si te encuentras en China, puedes encontrar un breve documento de uso de uv [aquí](../../ChinaUsers/uv.md).
> 2. Claude es la mejor opción para Stata-MCP, para usuarios chinos, recomiendo usar DeepSeek como proveedor de modelos ya que es económico y potente, y su puntuación es la más alta entre los proveedores chinos, si estás interesado, visita el informe [How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research).

### Instalación
Para la nueva versión, no necesitas instalar el paquete `stata-mcp` de nuevo; simplemente ejecuta los siguientes comandos para comprobar si tu equipo puede utilizarlo.
```bash
uvx stata-mcp --usable
uvx stata-mcp --version
```

Si deseas usarlo de forma local, puedes instalarlo mediante pip o descargar el código fuente y compilarlo.

**Instalar con pip**
```bash
pip install stata-mcp
```

**Descargar el código fuente y compilar**
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv build
```
A continuación, encontrarás el binario `stata-mcp` compilado en el directorio `dist`. Puedes usarlo directamente o añadirlo a tu PATH.

Por ejemplo:
```bash
uvx /path/to/your/whl/stata_mcp-1.13.0-py3-non-any.whl  # cambia el nombre del archivo según tu versión
```

## 📝 Documentación
- Para información más detallada sobre el uso, visita la [guía de Uso](../../Usages/Usage.md).
- Uso avanzado, visita la [Guía avanzada](../../Usages/Advanced.md)
- Algunas preguntas, visita las [Preguntas](../../Usages/Questions.md)
- Diferencia con [Stata-MCP@hanlulong](https://github.com/hanlulong/stata-mcp), visita las [Diferencias](../../Difference.md)

## 💡 Preguntas
- [Cherry Studio 32000 wrong](../../Usages/Questions.md#cherry-studio-32000-wrong)
- [Cherry Studio 32000 error](../../Usages/Questions.md#cherry-studio-32000-error)
- [Soporte para Windows](../../Usages/Questions.md#windows-supports)
- [Problemas de red](../../Usages/Questions.md#network-errors-when-running-stata-mcp)

## 🚀 Hoja de ruta
- [x] Soporte para macOS
- [x] Soporte para Windows
- [ ] Integraciones adicionales de LLM
- [ ] Optimizaciones de rendimiento

## ⚠️ Descargo de responsabilidad
Este proyecto es solo para fines de investigación. No soy responsable de ningún daño causado por este proyecto. Por favor, asegúrate de tener las licencias adecuadas para usar Stata.

Para más información, consulta la [Declaración](../../Rights/Statement.md).

## 🐛 Reportar problemas
Si encuentras algún error o tienes solicitudes de funciones, por favor [abre un issue](https://github.com/sepinetam/stata-mcp/issues/new).

## 📄 Licencia
[Apache License 2.0](../../../../LICENSE)

## 📚 Cita
Si utilizas Stata-MCP en tu investigación, por favor cita este repositorio utilizando uno de los siguientes formatos:

### BibTeX
```bibtex
@software{sepinetam2025stata,
  author = {Song Tan},
  title = {Stata-MCP: Let LLM help you achieve your regression analysis with Stata},
  year = {2025},
  url = {https://github.com/sepinetam/stata-mcp},
  version = {1.13.0}
}
```

### APA
```
Song Tan. (2025). Stata-MCP: Let LLM help you achieve your regression analysis with Stata (Version 1.13.0) [Computer software]. https://github.com/sepinetam/stata-mcp
```

### Chicago
```
Song Tan. 2025. "Stata-MCP: Let LLM help you achieve your regression analysis with Stata." Version 1.13.0. https://github.com/sepinetam/stata-mcp.
```

## 📬 Contacto
Correo electrónico: [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

¡O contribuye directamente enviando un [Pull Request](https://github.com/sepinetam/stata-mcp/pulls)! Damos la bienvenida a contribuciones de todo tipo, desde correcciones de errores hasta nuevas funcionalidades.

## ❤️ Agradecimientos
El autor agradece sinceramente al equipo oficial de Stata por su apoyo y a la Licencia Stata por autorizar el desarrollo de la prueba.

## ✨ Historial de Estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)