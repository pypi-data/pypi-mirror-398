# Coexistence - WhatsApp Business App Data Synchronization

Este módulo fornece endpoints para sincronizar dados do WhatsApp Business app quando usando o modo Coexistence.

## ⚠️ Importante

Após fazer o onboarding do cliente, você tem **24 horas** para sincronizar seus contatos e histórico de mensagens. Caso contrário, eles devem ser offboarded e completar o fluxo novamente.

**Nota:** Cada endpoint só pode ser executado **uma vez**. Se precisar executá-los novamente, o cliente deve primeiro fazer offboard e completar o fluxo de Embedded Signup novamente.

## Endpoints

### 1. Sincronizar Contatos

**POST** `/whatsapp-api-wrapper/embedded-signup/coexistence/sync-contacts/`

Inicia a sincronização de contatos do WhatsApp Business app.

#### Request

```json
{
  "phone_number_id": "123456789"
}
```

#### Response (Success)

```json
{
  "status": "success",
  "messaging_product": "whatsapp",
  "request_id": "abc123...",
  "message": "Contacts synchronization initiated. Webhooks will be triggered with contact data."
}
```

#### Webhooks Disparados

Se bem-sucedido, um conjunto de webhooks `smb_app_state_sync` será disparado descrevendo os contatos do WhatsApp no WhatsApp Business app do cliente.

Adições ou mudanças futuras nos contatos do WhatsApp do cliente também dispararão webhooks `smb_app_state_sync` correspondentes.

---

### 2. Sincronizar Histórico de Mensagens

**POST** `/whatsapp-api-wrapper/embedded-signup/coexistence/sync-history/`

Inicia a sincronização do histórico de mensagens do WhatsApp Business app.

#### Request

```json
{
  "phone_number_id": "123456789"
}
```

#### Response (Success)

```json
{
  "status": "success",
  "messaging_product": "whatsapp",
  "request_id": "xyz789...",
  "message": "Message history synchronization initiated. Webhooks will be triggered with message data."
}
```

#### Webhooks Disparados

**Se o cliente compartilhou o histórico:**
- Uma série de webhooks `history` será disparada, descrevendo cada mensagem enviada ou recebida de usuários do WhatsApp dentro de um período de tempo definido.

**Se o cliente NÃO compartilhou o histórico:**
- Um webhook `history` com error code `2593109` será disparado.

---

## Fluxo Recomendado

1. Complete o onboarding do cliente via Embedded Signup
2. Imediatamente após o onboarding, execute:
   - **Step 1:** Sincronizar contatos (`/sync-contacts/`)
   - **Step 2:** Sincronizar histórico (`/sync-history/`)
3. Processe os webhooks recebidos:
   - `smb_app_state_sync` - para contatos
   - `history` - para mensagens

## Requisitos

- O `WhatsAppCloudApiBusiness` deve ser do tipo `coexistence`
- Você deve ter subscrito aos webhooks da WABA durante o onboarding
- Você deve estar subscrito aos campos de webhook adicionais

## Armazenamento do Request ID

Recomendamos que você armazene o `request_id` retornado em cada resposta, caso precise contatar o suporte do WhatsApp.

## Exemplo de Uso

```python
import requests

# Sincronizar contatos
response = requests.post(
    'https://seu-backend.com/whatsapp-api-wrapper/embedded-signup/coexistence/sync-contacts/',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={'phone_number_id': '123456789'}
)

print(response.json())
# {'status': 'success', 'request_id': '...', ...}

# Sincronizar histórico
response = requests.post(
    'https://seu-backend.com/whatsapp-api-wrapper/embedded-signup/coexistence/sync-history/',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={'phone_number_id': '123456789'}
)

print(response.json())
# {'status': 'success', 'request_id': '...', ...}
```

## Erros Comuns

### 400 - Bad Request
```json
{
  "status": "error",
  "message": "This endpoint is only available for coexistence type businesses"
}
```
**Solução:** Certifique-se de que o `WhatsAppCloudApiBusiness` está configurado com `type='coexistence'`.

### 404 - Not Found
```json
{
  "status": "error",
  "message": "WhatsApp Business not found"
}
```
**Solução:** Verifique se o `phone_number_id` está correto e se o registro existe no banco de dados.

### 500 - Internal Server Error
```json
{
  "status": "error",
  "message": "Failed to initiate contacts synchronization",
  "details": {...}
}
```
**Solução:** Verifique os logs do servidor e os detalhes retornados. Pode ser um problema com o token de acesso ou com a API do Facebook.

