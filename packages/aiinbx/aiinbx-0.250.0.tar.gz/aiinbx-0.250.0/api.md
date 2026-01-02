# Threads

Types:

```python
from aiinbx.types import ThreadRetrieveResponse, ThreadForwardResponse, ThreadSearchResponse
```

Methods:

- <code title="get /threads/{threadId}">client.threads.<a href="./src/aiinbx/resources/threads.py">retrieve</a>(thread_id) -> <a href="./src/aiinbx/types/thread_retrieve_response.py">ThreadRetrieveResponse</a></code>
- <code title="post /threads/{threadId}/forward">client.threads.<a href="./src/aiinbx/resources/threads.py">forward</a>(thread_id, \*\*<a href="src/aiinbx/types/thread_forward_params.py">params</a>) -> <a href="./src/aiinbx/types/thread_forward_response.py">ThreadForwardResponse</a></code>
- <code title="post /threads/search">client.threads.<a href="./src/aiinbx/resources/threads.py">search</a>(\*\*<a href="src/aiinbx/types/thread_search_params.py">params</a>) -> <a href="./src/aiinbx/types/thread_search_response.py">ThreadSearchResponse</a></code>

# Emails

Types:

```python
from aiinbx.types import EmailRetrieveResponse, EmailReplyResponse, EmailSendResponse
```

Methods:

- <code title="get /emails/{emailId}">client.emails.<a href="./src/aiinbx/resources/emails.py">retrieve</a>(email_id) -> <a href="./src/aiinbx/types/email_retrieve_response.py">EmailRetrieveResponse</a></code>
- <code title="post /emails/{emailId}/reply">client.emails.<a href="./src/aiinbx/resources/emails.py">reply</a>(email_id, \*\*<a href="src/aiinbx/types/email_reply_params.py">params</a>) -> <a href="./src/aiinbx/types/email_reply_response.py">EmailReplyResponse</a></code>
- <code title="post /emails/send">client.emails.<a href="./src/aiinbx/resources/emails.py">send</a>(\*\*<a href="src/aiinbx/types/email_send_params.py">params</a>) -> <a href="./src/aiinbx/types/email_send_response.py">EmailSendResponse</a></code>

# Domains

Types:

```python
from aiinbx.types import (
    DomainCreateResponse,
    DomainRetrieveResponse,
    DomainListResponse,
    DomainDeleteResponse,
    DomainVerifyResponse,
)
```

Methods:

- <code title="post /domains">client.domains.<a href="./src/aiinbx/resources/domains.py">create</a>(\*\*<a href="src/aiinbx/types/domain_create_params.py">params</a>) -> <a href="./src/aiinbx/types/domain_create_response.py">DomainCreateResponse</a></code>
- <code title="get /domains/{domainId}">client.domains.<a href="./src/aiinbx/resources/domains.py">retrieve</a>(domain_id) -> <a href="./src/aiinbx/types/domain_retrieve_response.py">DomainRetrieveResponse</a></code>
- <code title="get /domains">client.domains.<a href="./src/aiinbx/resources/domains.py">list</a>() -> <a href="./src/aiinbx/types/domain_list_response.py">DomainListResponse</a></code>
- <code title="delete /domains/{domainId}">client.domains.<a href="./src/aiinbx/resources/domains.py">delete</a>(domain_id) -> <a href="./src/aiinbx/types/domain_delete_response.py">DomainDeleteResponse</a></code>
- <code title="post /domains/{domainId}/verify">client.domains.<a href="./src/aiinbx/resources/domains.py">verify</a>(domain_id) -> <a href="./src/aiinbx/types/domain_verify_response.py">DomainVerifyResponse</a></code>

# Webhooks

Types:

```python
from aiinbx.types import (
    InboundEmailReceivedWebhookEvent,
    OutboundEmailDeliveredWebhookEvent,
    OutboundEmailBouncedWebhookEvent,
    OutboundEmailComplainedWebhookEvent,
    OutboundEmailRejectedWebhookEvent,
    OutboundEmailOpenedWebhookEvent,
    OutboundEmailClickedWebhookEvent,
    UnwrapWebhookEvent,
)
```

# Meta

Types:

```python
from aiinbx.types import MetaWebhooksSchemaResponse
```

Methods:

- <code title="get /_meta/webhooks">client.meta.<a href="./src/aiinbx/resources/meta.py">webhooks_schema</a>() -> <a href="./src/aiinbx/types/meta_webhooks_schema_response.py">MetaWebhooksSchemaResponse</a></code>
