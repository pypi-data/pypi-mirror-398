# django-whatsapp-api-wrapper

> Importante: Esta biblioteca está em desenvolvimento ativo e ainda não possui cobertura de testes automatizados. As APIs podem mudar entre versões menores. Utilize com cautela em produção, valide os fluxos críticos e, se possível, contribua com issues/PRs.

Um wrapper simples para enviar mensagens via WhatsApp Cloud API e expor um endpoint de webhook, pronto para integrar em qualquer projeto Django.

## Instalação

```bash
python -m pip install django-whatsapp-api-wrapper
```

## Configuração (Django)

1) Adicione o app em `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_whatsapp_api_wrapper",
]
```

2) Inclua as URLs no `urls.py` principal:

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("whatsapp-api-wrapper/", include("django_whatsapp_api_wrapper.urls")),
]
```

3) Defina as variáveis de ambiente (ou no seu `.env`):

```bash
WHATSAPP_CLOUD_API_TOKEN=
WHATSAPP_CLOUD_API_PACKAGE_VERSION=0.1.1
WHATSAPP_CLOUD_API_VERSION=v23.0
WHATSAPP_CLOUD_API_PHONE_NUMBER_ID=
WHATSAPP_CLOUD_API_WABA_ID=
WHATSAPP_CLOUD_API_VERIFY_TOKEN=
```

4) Configure a autenticação para as rotas de templates (opcional, mas recomendado):

```python
# settings.py

# Opção 1: Usar Token Authentication do DRF (padrão)
WHATSAPP_API_AUTHENTICATION_CLASSES = [
    'rest_framework.authentication.TokenAuthentication',
]

# Opção 2: Usar JWT (se você já tem configurado)
WHATSAPP_API_AUTHENTICATION_CLASSES = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]

# Opção 3: Usar API Key simples
WHATSAPP_API_AUTHENTICATION_CLASSES = [
    'django_whatsapp_api_wrapper.authentication.APIKeyAuthentication',
]
WHATSAPP_API_KEY = "sua_api_key_secreta_aqui"

# Permissões (padrão: IsAuthenticated)
WHATSAPP_API_PERMISSION_CLASSES = [
    'rest_framework.permissions.IsAuthenticated',
]
```

**Importante:** Se não configurar a autenticação, as rotas de templates usarão `TokenAuthentication` por padrão. As rotas de mensagens herdam a mesma configuração.

O endpoint de webhook ficará disponível em:

- GET/POST: `/whatsapp-api-wrapper/webhook/`
- Verificação (GET): `/whatsapp-api-wrapper/webhook/?hub.mode=subscribe&hub.verify_token=<TOKEN>&hub.challenge=123`

## Extensibilidade do Webhook

Você pode customizar o processamento do webhook no projeto hospedeiro de duas formas:

- Via setting com handler plugável:

```python
# settings.py
WHATSAPP_WEBHOOK_HANDLER = "meuapp.whatsapp.handle_webhook"
```

```python
# meuapp/whatsapp.py
from django.http import JsonResponse

def handle_webhook(request, payload):
    # sua lógica aqui (salvar eventos, acionar tasks, etc)
    return JsonResponse({"ok": True})
```

- Via signal `webhook_event_received`:

```python
from django.dispatch import receiver
from django_whatsapp_api_wrapper.signals import webhook_event_received

@receiver(webhook_event_received)
def on_whatsapp_event(sender, payload, request, **kwargs):
    # sua lógica aqui
    pass
```

## Mensagens

Envio e recebimento de mensagens via Cloud API.

### Envio (Python)

```python
from django_whatsapp_api_wrapper import WhatsApp
from django_whatsapp_api_wrapper.messages import types as WATypes

wp = WhatsApp()

# Texto (construa o objeto e passe o objeto diretamente)
text = WATypes.Text(body="olá do wrapper", preview_url=False)
m_text = wp.build_message(to="551199999999", type="text", data=text)
m_text.send()

# Template
tpl = WATypes.Template(name="opa", language={"code": "pt_BR"}, components=[])
m_tpl = wp.build_message(to="551199999999", type="template", data=tpl)
m_tpl.send()

# Sticker (exemplo com media ID)
stk = WATypes.Sticker(id="MEDIA_ID")
m_stk = wp.build_message(to="551199999999", type="sticker", data=stk)
m_stk.send()

# Imagem por URL
img = WATypes.Image(link="https://exemplo.com/foto.jpg", caption="Legenda")
m_img = wp.build_message(to="551199999999", type="image", data=img)
m_img.send()
```

### Webhook

- Recebe eventos (mensagens/atualizações de status) em `GET/POST /whatsapp-api-wrapper/webhook/`.
- Verificação (GET): `/whatsapp-api-wrapper/webhook/?hub.mode=subscribe&hub.verify_token=<TOKEN>&hub.challenge=123`.
- Personalize via setting `WHATSAPP_WEBHOOK_HANDLER` ou escute o signal `webhook_event_received` (veja seção Extensibilidade do Webhook acima).

---

## Endpoints HTTP de Mensagens (DRF)

Prefixo base: `/whatsapp-api-wrapper/messages/`

**⚠️ Importante:** Todos os endpoints de mensagens requerem autenticação (veja seção Autenticação acima).

1) Enviar mensagem (genérico)

POST `/whatsapp-api-wrapper/messages/send/`

Body (exemplos por tipo):

Texto
```json
{ "to": "551199999999", "type": "text", "text": {"preview_url": false, "body": "Olá!"} }
```

Texto (reply)
```json
{ "to": "551199999999", "type": "text", "context": {"message_id": "wamid.xxx"}, "text": {"body": "Resposta"} }
```

Template
```json
{ "to": "551199999999", "type": "template", "template": {"name": "opa", "language": {"code": "pt_BR"}, "components": []} }
```

Imagem por URL
```json
{ "to": "551199999999", "type": "image", "image": {"link": "https://exemplo.com/foto.jpg", "caption": "Legenda"} }
```

2) Enviar texto

POST `/whatsapp-api-wrapper/messages/text/`
```json
{ "to": "551199999999", "body": "Olá!", "preview_url": false }
```

**Exemplo com curl:**
```bash
curl -X POST \
  -H "Authorization: Token seu_token_aqui" \
  -H "Content-Type: application/json" \
  -d '{"to": "551199999999", "body": "Olá!", "preview_url": false}' \
  "$BASE/whatsapp-api-wrapper/messages/text/"
```

3) Responder com texto

POST `/whatsapp-api-wrapper/messages/text/reply/`
```json
{ "to": "551199999999", "reply_to": "wamid.xxx", "body": "Resposta", "preview_url": false }
```

4) Enviar template

POST `/whatsapp-api-wrapper/messages/template/`
```json
{ "to": "551199999999", "name": "opa", "language": {"code": "pt_BR"}, "components": [] }
```

Respostas: mesmas do Graph (inclui `messages[0].id` com prefixo `wamid`).

---

### Mensagens por tipo (Python + HTTP)

Observação: Para todos os tipos abaixo você pode:
- Python: instanciar o objeto em `django_whatsapp_api_wrapper.messages.types` e passar diretamente como `data=<objeto>` no `build_message`.
- HTTP: usar o endpoint genérico `POST /whatsapp-api-wrapper/messages/send/` com `type=<tipo>` e o objeto correspondente no corpo.
- Atalhos existentes: `text/`, `text/reply/`, `template/`.

#### Texto
- Python:
```python
text = WATypes.Text(body="Olá!", preview_url=False)
wp.build_message(to="551199999999", type="text", data=text).send()
```
- HTTP (atalho): `POST /messages/text/`
```json
{ "to": "551199999999", "body": "Olá!", "preview_url": false }
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "text", "text": {"body": "Olá!", "preview_url": false} }
```

#### Texto (reply)
- Python:
```python
text = WATypes.Text(body="Resposta")
wp.build_message(to="551199999999", type="text", data=text).send()
# Para reply via HTTP use context.message_id
```
- HTTP (atalho): `POST /messages/text/reply/`
```json
{ "to": "551199999999", "reply_to": "wamid.xxx", "body": "Resposta", "preview_url": false }
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "text", "context": {"message_id": "wamid.xxx"}, "text": {"body": "Resposta"} }
```

#### Template
- Python:
```python
tpl = WATypes.Template(name="opa", language={"code": "pt_BR"}, components=[])
wp.build_message(to="551199999999", type="template", data=tpl).send()
```
- HTTP (atalho): `POST /messages/template/`
```json
{ "to": "551199999999", "name": "opa", "language": {"code": "pt_BR"}, "components": [] }
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "template", "template": {"name": "opa", "language": {"code": "pt_BR"}, "components": []} }
```

#### Imagem
- Python:
```python
img = WATypes.Image(link="https://exemplo.com/foto.jpg", caption="Legenda")
wp.build_message(to="551199999999", type="image", data=img).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "image", "image": {"link": "https://exemplo.com/foto.jpg", "caption": "Legenda"} }
```

#### Áudio
- Python:
```python
aud = WATypes.Audio(id="MEDIA_ID")  # ou link="https://..."
wp.build_message(to="551199999999", type="audio", data=aud).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "audio", "audio": {"id": "MEDIA_ID"} }
```

#### Documento
- Python:
```python
doc = WATypes.Document(link="https://exemplo.com/arquivo.pdf", filename="arquivo.pdf")
wp.build_message(to="551199999999", type="document", data=doc).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "document", "document": {"link": "https://exemplo.com/arquivo.pdf", "filename": "arquivo.pdf"} }
```

#### Vídeo
- Python:
```python
vid = WATypes.Video(id="MEDIA_ID", caption="Demo")
wp.build_message(to="551199999999", type="video", data=vid).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "video", "video": {"id": "MEDIA_ID", "caption": "Demo"} }
```

#### Sticker
- Python:
```python
stk = WATypes.Sticker(id="MEDIA_ID")
wp.build_message(to="551199999999", type="sticker", data=stk).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "sticker", "sticker": {"id": "MEDIA_ID"} }
```

#### Localização
- Python:
```python
loc = WATypes.Location(latitude=-23.56, longitude=-46.63, name="SP", address="Av. Paulista")
wp.build_message(to="551199999999", type="location", data=loc).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "location", "location": {"latitude": -23.56, "longitude": -46.63, "name": "SP", "address": "Av. Paulista"} }
```

#### Contacts
- Python:
```python
contact = WATypes.Contact(name={"formatted_name": "Maria"}, phones=[{"phone": "+551199999999", "type": "CELL"}])
wp.build_message(to="551199999999", type="contacts", data=[contact]).send()  # lista de contatos
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "contacts", "contacts": [{ "name": {"formatted_name": "Maria"}, "phones": [{"phone": "+551199999999", "type": "CELL"}] }] }
```

#### Reaction
- Python:
```python
react = WATypes.Reaction(message_id="wamid.xxx", emoji="😀")
wp.build_message(to="551199999999", type="reaction", data=react).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "reaction", "reaction": {"message_id": "wamid.xxx", "emoji": "😀"} }
```

#### Interativo (Reply Buttons)
- Python:
```python
interactive = WATypes.Interactive(
    type="button",
    header={"type": "text", "text": "Título"},
    body={"text": "Mensagem"},
    footer={"text": "Rodapé"},
    action={"buttons": [{"title": "OK", "id": "ok"}, {"title": "Cancelar", "id": "cancel"}]}
)
wp.build_message(to="551199999999", type="interactive", data=interactive).send()
```
- HTTP (genérico): `POST /messages/send/`
```json
{ "to": "551199999999", "type": "interactive", "interactive": {
  "type": "button",
  "header": {"type": "text", "text": "Título"},
  "body": {"text": "Mensagem"},
  "footer": {"text": "Rodapé"},
  "action": {"buttons": [
    {"type": "reply", "title": "OK", "id": "ok"},
    {"type": "reply", "title": "Cancelar", "id": "cancel"}
  ]}
} }
```

## Autenticação

### Proteção das Rotas de API

Por padrão, todas as rotas de templates (`/templates/`) e mensagens (`/messages/`) são protegidas e requerem autenticação. O webhook permanece público (necessário para o WhatsApp).

### Opções de Autenticação

#### 1. Token Authentication (Padrão)
```python
# settings.py
WHATSAPP_API_AUTHENTICATION_CLASSES = [
    'rest_framework.authentication.TokenAuthentication',
]
```

Uso:
```bash
curl -H "Authorization: Token seu_token_aqui" \
     "$BASE/whatsapp-api-wrapper/templates/"
```

#### 2. JWT Authentication
```python
# settings.py
WHATSAPP_API_AUTHENTICATION_CLASSES = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]
```

Uso:
```bash
curl -H "Authorization: Bearer seu_jwt_token" \
     "$BASE/whatsapp-api-wrapper/templates/"
```

#### 3. API Key Authentication
```python
# settings.py
WHATSAPP_API_AUTHENTICATION_CLASSES = [
    'django_whatsapp_api_wrapper.authentication.APIKeyAuthentication',
]
WHATSAPP_API_KEY = "sua_api_key_secreta"
```

Uso:
```bash
curl -H "X-WhatsApp-API-Key: sua_api_key_secreta" \
     "$BASE/whatsapp-api-wrapper/templates/"
```

#### 4. Múltiplas Autenticações
```python
# settings.py
WHATSAPP_API_AUTHENTICATION_CLASSES = [
    'rest_framework.authentication.TokenAuthentication',
    'django_whatsapp_api_wrapper.authentication.APIKeyAuthentication',
]
```

### Permissões Customizadas
```python
# settings.py
WHATSAPP_API_PERMISSION_CLASSES = [
    'rest_framework.permissions.IsAuthenticated',
    # ou 'rest_framework.permissions.IsAdminUser',
    # ou 'myapp.permissions.CustomPermission',
]
```

## Templates

Endpoints REST (DRF) para gerenciar Message Templates do WhatsApp (proxy para Graph API). Todos os endpoints abaixo partem do prefixo que você incluir no projeto, por exemplo: `.../whatsapp-api-wrapper/`.

**⚠️ Importante:** Todos os endpoints de templates requerem autenticação (veja seção Autenticação acima).

Requisitos de ambiente: `WHATSAPP_CLOUD_API_TOKEN`, `WHATSAPP_CLOUD_API_VERSION`, `WHATSAPP_CLOUD_API_WABA_ID`.

Aqui a documentação OFICIAL: 

https://www.postman.com/meta/whatsapp-business-platform/folder/2ksdd2s/whatsapp-cloud-api

### Listar e criar

- GET `GET /templates/?limit=&after=&before=`
- POST `POST /templates/` com payload conforme a Graph API.

Exemplo de criação:

```bash
curl -X POST \
  "$BASE/whatsapp-api-wrapper/templates/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "authentication_code_copy_code_button",
    "language": "en_US",
    "category": "AUTHENTICATION",
    "components": [
      {"type": "BODY", "add_security_recommendation": true},
      {"type": "FOOTER", "code_expiration_minutes": 10},
      {"type": "BUTTONS", "buttons": [{"type": "OTP", "otp_type": "COPY_CODE", "text": "Copy Code"}]}
    ]
  }'
```

### Buscar por ID e editar

- GET `GET /templates/<template_id>/`
- POST `POST /templates/<template_id>/` para editar (mesmo formato do corpo de criação).

### Buscar e excluir por nome

- GET `GET /templates/by-name/?name=<TEMPLATE_NAME>`
- DELETE `DELETE /templates/by-name/?name=<TEMPLATE_NAME>`

### Excluir por ID (hsm_id) e nome

- DELETE `DELETE /templates/delete-by-id/?hsm_id=<HSM_ID>&name=<NAME>`

### Obter namespace

- GET `GET /templates/namespace/`

Notas:
- Os payloads aceitos seguem a documentação oficial de Message Templates da Meta (Graph API). Este wrapper só valida campos básicos e encaminha a requisição.
- As respostas retornadas são as mesmas da Graph API (status code e corpo JSON), para facilitar troubleshooting.

## Notas

- Nome do pacote no PyPI: `django-whatsapp-api-wrapper`
- Nome do módulo/import: `django_whatsapp_api_wrapper`